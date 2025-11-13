"""
Initialize strain database with public datasets on first launch.

Downloads and imports:
1. Terpene Profile Parser dataset (GitHub)
2. Mendeley 800+ strain dataset (if available)

Creates a marker file to prevent re-downloading on subsequent launches.
"""

import os
import csv
import httpx
import asyncio
from pathlib import Path
from typing import Dict, List
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import Profile
from app.services.classifier import classify_terpene_profile
from app.models.schemas import Totals


DATASETS_DIR = Path(__file__).parent / "downloads"
INIT_MARKER = DATASETS_DIR / ".initialized"

# Dataset sources
TERPENE_PARSER_CSV = "https://raw.githubusercontent.com/MaxValue/Terpene-Profile-Parser-for-Cannabis-Strains/master/results.csv"


def is_initialized() -> bool:
    """Check if datasets have already been loaded."""
    return INIT_MARKER.exists()


def mark_initialized():
    """Create marker file to indicate datasets have been loaded."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    INIT_MARKER.touch()
    print("✓ Marked database as initialized")


async def download_file(url: str, filename: str) -> Path:
    """Download a file from URL to local storage."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATASETS_DIR / filename

    if filepath.exists():
        print(f"  File already exists: {filename}")
        return filepath

    print(f"  Downloading {filename}...")
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

        filepath.write_bytes(response.content)
        print(f"  ✓ Downloaded {filename} ({len(response.content)} bytes)")

    return filepath


def parse_terpene_parser_csv(filepath: Path) -> List[Dict]:
    """Parse the Terpene Profile Parser CSV file."""
    print(f"\nParsing {filepath.name}...")
    strains = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Debug: Print column names
        print(f"  CSV columns: {reader.fieldnames}")

        for row in reader:
            # Skip rows without sample name
            if not row.get('Sample Name') or not row.get('Sample Name').strip():
                continue

            strain_name = row['Sample Name'].strip()

            # Extract terpene percentages
            terpenes = {}
            terpene_fields = {
                'beta-Myrcene': 'myrcene',
                'delta-Limonene': 'limonene',
                'beta-Caryophyllene': 'caryophyllene',
                'alpha-Pinene': 'alpha_pinene',
                'beta-Pinene': 'beta_pinene',
                'Terpinolene': 'terpinolene',
                'alpha-Humulene': 'humulene',
                'Linalool': 'linalool',
                'Ocimene': 'ocimene',
            }

            for csv_field, standard_name in terpene_fields.items():
                if csv_field in row and row[csv_field]:
                    try:
                        value_str = row[csv_field].strip()
                        if not value_str:
                            continue
                        value = float(value_str)
                        # Values are already percentages (59.5 = 59.5%), convert to fraction
                        if value > 1:
                            value = value / 100
                        if value > 0:
                            terpenes[standard_name] = value
                    except (ValueError, AttributeError, TypeError):
                        continue

            # Extract cannabinoids if available
            totals = Totals()
            cannabinoid_fields = {
                'delta-9 THC': 'thc',
                'delta-9 THC-A': 'thca',
                'THC-A': 'thca',  # Alternative name
                'CBD': 'cbd',
                'CBD-A': 'cbda',
                'CBN': 'cbn',
                'delta-9 CBG': 'cbg',
            }

            for csv_field, standard_name in cannabinoid_fields.items():
                if csv_field in row and row[csv_field]:
                    try:
                        value_str = row[csv_field].strip()
                        if not value_str:
                            continue
                        value = float(value_str)
                        # Values are already percentages, convert to fraction
                        if value > 1:
                            value = value / 100
                        if value > 0:
                            setattr(totals, standard_name, value)
                    except (ValueError, AttributeError, TypeError):
                        continue

            # Only add if we have at least some terpene data
            if terpenes:
                strains.append({
                    'name': strain_name,
                    'terpenes': terpenes,
                    'totals': totals
                })

    print(f"  ✓ Parsed {len(strains)} strains with terpene data")
    return strains


def import_strains_to_db(strains: List[Dict], source: str = 'dataset_import'):
    """Import strain data into PostgreSQL profiles table."""
    print(f"\nImporting {len(strains)} strains to database...")

    db = SessionLocal()
    imported_count = 0
    skipped_count = 0

    try:
        for strain_data in strains:
            strain_name = strain_data['name']
            terpenes = strain_data['terpenes']
            totals = strain_data['totals']

            # Normalize strain name for lookup
            normalized_name = strain_name.lower()
            normalized_name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in normalized_name)
            normalized_name = ' '.join(normalized_name.split()).strip()

            # Check if strain already exists
            existing = db.query(Profile).filter(
                Profile.strain_normalized == normalized_name
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Classify terpene profile
            category = classify_terpene_profile(terpenes) if terpenes else None

            # Create profile
            # Convert Totals model to dict (use model_dump for Pydantic v2)
            try:
                totals_dict = totals.model_dump()
            except AttributeError:
                totals_dict = totals.dict()  # Fallback for Pydantic v1

            profile = Profile(
                strain_normalized=normalized_name,
                terp_vector=terpenes,
                totals=totals_dict,
                category=category,
                provenance={
                    'source': source,
                    'import_method': 'initial_dataset_load',
                    'original_dataset': 'terpene_parser',
                    'strain_name': strain_name  # Store original name in provenance
                }
            )

            db.add(profile)
            imported_count += 1

            # Commit in batches
            if imported_count % 100 == 0:
                db.commit()
                print(f"  Imported {imported_count} strains...")

        db.commit()
        print(f"  ✓ Successfully imported {imported_count} new strains")
        if skipped_count > 0:
            print(f"  → Skipped {skipped_count} existing strains")

    except Exception as e:
        print(f"  ✗ Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def initialize_datasets():
    """Main initialization function - downloads and imports datasets."""

    if is_initialized():
        print("✓ Database already initialized with datasets")
        return

    print("=" * 60)
    print("INITIALIZING STRAIN DATABASE WITH PUBLIC DATASETS")
    print("=" * 60)

    try:
        # Download Terpene Profile Parser dataset
        print("\n1. Downloading Terpene Profile Parser dataset...")
        csv_path = await download_file(TERPENE_PARSER_CSV, "terpene_parser.csv")

        # Parse CSV
        strains = parse_terpene_parser_csv(csv_path)

        # Import to database
        import_strains_to_db(strains, source='dataset_import')

        # Mark as complete
        mark_initialized()

        print("\n" + "=" * 60)
        print("✓ DATASET INITIALIZATION COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Dataset initialization failed: {e}")
        print("  The application will continue without pre-loaded data.")
        print("  Data will be collected as users search.")


def run_initialization():
    """Synchronous wrapper for async initialization."""
    asyncio.run(initialize_datasets())


if __name__ == "__main__":
    run_initialization()
