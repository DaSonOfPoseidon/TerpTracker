"""
Initialize strain database with public datasets on first launch.

Downloads and imports:
1. Terpene Profile Parser dataset (GitHub) - ~32,874 strains
2. Phytochemical Diversity dataset (GitHub) - ~3,088 unique strains
3. OpenTHC Variety Database (name normalization)
4. Cannlytics Cannabis Results (HuggingFace) - state-by-state lab results

Each dataset has an independent marker file to prevent re-downloading.
"""

import csv
import json
import httpx
import asyncio
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import Profile
from app.services.classifier import classify_terpene_profile
from app.models.schemas import Totals
from app.core.constants import TERPENE_FIELD_MAP, CANNABINOID_FIELD_MAP
from app.utils.conversions import safe_float, safe_terpene_value
from app.utils.normalization import normalize_strain_name


DATASETS_DIR = Path(__file__).parent / "downloads"

# Per-dataset initialization markers
MARKERS = {
    'terpene_parser':     DATASETS_DIR / ".initialized_terpene_parser",
    'phytochem':          DATASETS_DIR / ".initialized_phytochem",
    'openthc_varieties':  DATASETS_DIR / ".initialized_openthc",
    'cannlytics_results': DATASETS_DIR / ".initialized_cannlytics",
}

# Legacy marker (treated as terpene_parser being done)
LEGACY_MARKER = DATASETS_DIR / ".initialized"

# Dataset URLs
TERPENE_PARSER_CSV = "https://raw.githubusercontent.com/MaxValue/Terpene-Profile-Parser-for-Cannabis-Strains/master/results.csv"
PHYTOCHEM_CSV = "https://raw.githubusercontent.com/cjsmith015/phytochemical-diversity-cannabis/main/data/preproc_lab_data_pub_20220218.csv"
OPENTHC_STRAINS_JSON = "https://vdb.openthc.org/download/strains.json"

# Cannlytics HuggingFace CSV URL pattern
CANNLYTICS_BASE = "https://huggingface.co/datasets/cannlytics/cannabis_results/resolve/main/data"

# States with usable terpene data, ordered small -> large
# Removed: HI, RI, MA, OR, MD, MI (no individual terpene breakdowns or no strain names)
# Excluded: WA (XLSX only)
CANNLYTICS_STATES = [
    ("ny", "New York"),
    ("ut", "Utah"),
    ("ct", "Connecticut"),
    ("co", "Colorado"),
    ("fl", "Florida"),
    ("nv", "Nevada"),
    ("ca", "California"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_dataset_initialized(key: str) -> bool:
    """Check if a specific dataset has already been loaded."""
    # Legacy marker counts as terpene_parser
    if key == 'terpene_parser' and LEGACY_MARKER.exists():
        return True
    marker = MARKERS.get(key)
    return marker is not None and marker.exists()


def mark_dataset_initialized(key: str):
    """Create marker file for a specific dataset."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    marker = MARKERS.get(key)
    if marker:
        marker.touch()
        print(f"  ✓ Marked {key} as initialized")


def is_initialized() -> bool:
    """Legacy check - True if terpene_parser is done."""
    return is_dataset_initialized('terpene_parser')


def mark_initialized():
    """Legacy marker - marks terpene_parser as done."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_MARKER.touch()
    mark_dataset_initialized('terpene_parser')
    print("✓ Marked database as initialized")


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

async def download_file(url: str, filename: str, timeout: float = 120.0, stream: bool = False, max_retries: int = 3) -> Path:
    """
    Download a file from URL to local storage.

    Args:
        url: Source URL
        filename: Local filename to save as
        timeout: Request timeout in seconds (default 120s)
        stream: Use streaming download for large files
        max_retries: Number of retry attempts on failure
    """
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATASETS_DIR / filename

    if filepath.exists():
        print(f"  File already exists: {filename}")
        return filepath

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Downloading {filename} (attempt {attempt}/{max_retries})...")
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                if stream:
                    # Streaming download for large files
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        total = 0
                        with open(filepath, 'wb') as f:
                            async for chunk in response.aiter_bytes(chunk_size=65536):
                                f.write(chunk)
                                total += len(chunk)
                        print(f"  ✓ Downloaded {filename} ({total:,} bytes)")
                else:
                    response = await client.get(url)
                    response.raise_for_status()
                    filepath.write_bytes(response.content)
                    print(f"  ✓ Downloaded {filename} ({len(response.content):,} bytes)")

            return filepath

        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  ⚠ Download failed: {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
                # Clean up partial file
                if filepath.exists():
                    filepath.unlink()
            else:
                print(f"  ✗ Download failed after {max_retries} attempts: {e}")
                if filepath.exists():
                    filepath.unlink()
                raise

    return filepath  # Should not reach here


# ---------------------------------------------------------------------------
# Parser: Terpene Profile Parser (existing)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Parser: Phytochemical Diversity dataset
# ---------------------------------------------------------------------------

def parse_phytochem_csv(filepath: Path) -> List[Dict]:
    """
    Parse the Phytochemical Diversity of Cannabis CSV.

    Source: cjsmith015/phytochemical-diversity-cannabis
    ~89,923 rows of lab test results, aggregated by strain_slug to ~3,088 unique strains.
    Values are absolute weight percentages (e.g., 0.177 = 0.177%).
    """
    print(f"\nParsing {filepath.name} (Phytochemical Diversity)...")

    terpene_columns = {
        'myrcene': 'myrcene',
        'limonene': 'limonene',
        'caryophyllene': 'caryophyllene',
        'a_pinene': 'alpha_pinene',
        'b_pinene': 'beta_pinene',
        'terpinolene': 'terpinolene',
        'humulene': 'humulene',
        'linalool': 'linalool',
        'tot_ocimene': 'ocimene',
        'bisabolol': 'bisabolol',
        'camphene': 'camphene',
        'g_terpinene': 'gamma_terpinene',
        'a_terpinene': 'alpha_terpinene',
        'tot_nerolidol_ct': 'nerolidol',
    }

    cannabinoid_columns = {
        'tot_thc': 'thc',
        'tot_cbd': 'cbd',
        'tot_cbg': 'cbg',
        'tot_cbc': 'cbc',
        'tot_cbn': 'cbn',
        'tot_thcv': 'thcv',
    }

    # Accumulate all samples per strain for averaging
    strain_samples = defaultdict(list)
    rows_read = 0
    rows_with_terps = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows_read += 1
            strain_slug = (row.get('strain_slug') or '').strip()
            if not strain_slug:
                continue

            # Check if this row has terpene data
            has_terps = row.get('has_terps', '').strip()
            if has_terps == '0' or has_terps == 'False':
                continue

            # Extract terpene values
            terpenes = {}
            for csv_col, std_name in terpene_columns.items():
                val = safe_float(row.get(csv_col))
                if val is not None:
                    terpenes[std_name] = val

            if not terpenes:
                continue

            rows_with_terps += 1

            # Extract cannabinoid values
            cannabinoids = {}
            for csv_col, std_name in cannabinoid_columns.items():
                val = safe_float(row.get(csv_col))
                if val is not None:
                    cannabinoids[std_name] = val

            strain_samples[strain_slug].append({
                'terpenes': terpenes,
                'cannabinoids': cannabinoids,
            })

    print(f"  Read {rows_read:,} rows, {rows_with_terps:,} with terpene data")
    print(f"  Found {len(strain_samples):,} unique strains")

    # Aggregate by strain (mean of all samples)
    strains = []
    for slug, samples in strain_samples.items():
        # Average terpenes across all samples
        terp_sums = defaultdict(float)
        terp_counts = defaultdict(int)
        for sample in samples:
            for name, val in sample['terpenes'].items():
                terp_sums[name] += val
                terp_counts[name] += 1

        avg_terpenes = {}
        for name in terp_sums:
            avg_terpenes[name] = terp_sums[name] / terp_counts[name]

        # Average cannabinoids
        cann_sums = defaultdict(float)
        cann_counts = defaultdict(int)
        for sample in samples:
            for name, val in sample['cannabinoids'].items():
                cann_sums[name] += val
                cann_counts[name] += 1

        totals = Totals()
        for name in cann_sums:
            avg_val = cann_sums[name] / cann_counts[name]
            if avg_val > 0:
                # Cannabinoid values are in % (e.g., 20.5 = 20.5%), convert to fraction
                setattr(totals, name, avg_val / 100 if avg_val > 1 else avg_val)

        # Convert slug back to a readable name: "blue-dream" -> "Blue Dream"
        strain_name = slug.replace('-', ' ').replace('_', ' ').title()

        strains.append({
            'name': strain_name,
            'terpenes': avg_terpenes,
            'totals': totals,
            'sample_count': len(samples),
        })

    print(f"  ✓ Parsed {len(strains):,} unique strains (averaged from {rows_with_terps:,} samples)")
    return strains


# ---------------------------------------------------------------------------
# Parser: Cannlytics Cannabis Results (HuggingFace, state-by-state)
# ---------------------------------------------------------------------------

def parse_cannlytics_state_csv(filepath: Path, state: str) -> List[Dict]:
    """
    Parse a Cannlytics state-level lab results CSV.

    Each CSV has hundreds of columns; we extract strain name, terpenes, and cannabinoids.
    Multiple lab results per strain are aggregated by mean.
    """
    print(f"\n  Parsing {filepath.name} ({state})...")

    # Use shared field maps (already include all keys needed for Cannlytics CSVs)
    terpene_columns = TERPENE_FIELD_MAP
    cannabinoid_columns = CANNABINOID_FIELD_MAP

    strain_samples = defaultdict(list)
    rows_read = 0
    rows_with_data = 0

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print(f"  ⚠ Empty or invalid CSV: {filepath.name}")
            return []

        # Find which terpene/cannabinoid columns actually exist in this file
        available_terp_cols = {col: std for col, std in terpene_columns.items() if col in reader.fieldnames}
        available_cann_cols = {col: std for col, std in cannabinoid_columns.items() if col in reader.fieldnames}

        for row in reader:
            rows_read += 1
            strain_name = (row.get('strain_name') or '').strip()
            if not strain_name:
                strain_name = (row.get('product_name') or '').strip()
            if not strain_name:
                continue

            # Extract terpenes
            terpenes = {}
            for csv_col, std_name in available_terp_cols.items():
                val = safe_float(row.get(csv_col))
                if val is not None:
                    # Keep highest value if multiple columns map to same name
                    if std_name not in terpenes or val > terpenes[std_name]:
                        terpenes[std_name] = val

            # Extract cannabinoids
            cannabinoids = {}
            for csv_col, std_name in available_cann_cols.items():
                val = safe_float(row.get(csv_col))
                if val is not None:
                    if std_name not in cannabinoids or val > cannabinoids[std_name]:
                        cannabinoids[std_name] = val

            # Fallback: parse 'results' JSON column when individual columns had no terpenes
            if not terpenes:
                results_raw = (row.get('results') or '').strip()
                if results_raw:
                    try:
                        results_list = json.loads(results_raw)
                        for entry in results_list:
                            if not isinstance(entry, dict):
                                continue
                            analysis = (entry.get('analysis') or '').lower()
                            key = entry.get('key', '')
                            val = safe_float(entry.get('value'))
                            if val is None:
                                continue
                            if analysis == 'terpenes' and key in terpene_columns:
                                std_name = terpene_columns[key]
                                if std_name not in terpenes or val > terpenes[std_name]:
                                    terpenes[std_name] = val
                            elif analysis == 'cannabinoids' and key in cannabinoid_columns:
                                std_name = cannabinoid_columns[key]
                                if std_name not in cannabinoids or val > cannabinoids[std_name]:
                                    cannabinoids[std_name] = val
                    except (json.JSONDecodeError, TypeError):
                        pass

            if not terpenes:
                continue

            rows_with_data += 1
            strain_samples[strain_name].append({
                'terpenes': terpenes,
                'cannabinoids': cannabinoids,
            })

    print(f"    Read {rows_read:,} rows, {rows_with_data:,} with terpene data")
    print(f"    Found {len(strain_samples):,} unique strains")

    # Aggregate by strain (mean)
    strains = []
    for name, samples in strain_samples.items():
        terp_sums = defaultdict(float)
        terp_counts = defaultdict(int)
        for sample in samples:
            for tname, val in sample['terpenes'].items():
                terp_sums[tname] += val
                terp_counts[tname] += 1

        avg_terpenes = {}
        for tname in terp_sums:
            avg_terpenes[tname] = terp_sums[tname] / terp_counts[tname]

        cann_sums = defaultdict(float)
        cann_counts = defaultdict(int)
        for sample in samples:
            for cname, val in sample['cannabinoids'].items():
                cann_sums[cname] += val
                cann_counts[cname] += 1

        totals = Totals()
        for cname in cann_sums:
            avg_val = cann_sums[cname] / cann_counts[cname]
            if avg_val > 0:
                # Values are percentages (e.g., 23.5 = 23.5%), convert to fraction
                setattr(totals, cname, avg_val / 100 if avg_val > 1 else avg_val)

        strains.append({
            'name': name,
            'terpenes': avg_terpenes,
            'totals': totals,
            'sample_count': len(samples),
        })

    print(f"    ✓ Parsed {len(strains):,} unique strains from {state}")
    return strains


# ---------------------------------------------------------------------------
# Parser: OpenTHC Variety Database
# ---------------------------------------------------------------------------

def parse_openthc_varieties(filepath: Path) -> Dict[str, str]:
    """
    Parse OpenTHC strains.json for strain name normalization.

    Returns a dict mapping stub (normalized) -> canonical display name.
    Also saves the mapping as strain_alias_map.json for runtime use.
    """
    print(f"\nParsing {filepath.name} (OpenTHC Varieties)...")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Build stub -> canonical name mapping
    stub_map = {}
    for entry in data:
        name = (entry.get('name') or '').strip()
        stub = (entry.get('stub') or '').strip()
        if name and stub:
            stub_map[stub] = name

    # Save mapping for runtime use
    alias_path = DATASETS_DIR / "strain_alias_map.json"
    with open(alias_path, 'w', encoding='utf-8') as f:
        json.dump(stub_map, f, indent=2)

    print(f"  ✓ Parsed {len(stub_map):,} strain name mappings")
    print(f"  ✓ Saved alias map to {alias_path.name}")
    return stub_map


# ---------------------------------------------------------------------------
# Database import
# ---------------------------------------------------------------------------

def import_strains_to_db(strains: List[Dict], source: str = 'dataset_import',
                         original_dataset: str = 'unknown', batch_size: int = 200):
    """
    Import strain data into PostgreSQL profiles table.

    Args:
        strains: List of dicts with 'name', 'terpenes', 'totals' keys
        source: Source identifier for provenance
        original_dataset: Name of the originating dataset
        batch_size: Number of records per commit batch
    """
    print(f"\nImporting {len(strains):,} strains to database (source={source}, dataset={original_dataset})...")

    db = SessionLocal()
    imported_count = 0
    skipped_count = 0

    try:
        for strain_data in strains:
            strain_name = strain_data['name']
            terpenes = strain_data['terpenes']
            totals = strain_data['totals']

            # Normalize strain name for lookup
            normalized_name = normalize_strain_name(strain_name)

            if not normalized_name:
                skipped_count += 1
                continue

            # Check if strain already exists
            existing = db.query(Profile).filter(
                Profile.strain_normalized == normalized_name
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Classify terpene profile
            category = classify_terpene_profile(terpenes) if terpenes else None

            # Convert Totals model to dict
            try:
                totals_dict = totals.model_dump()
            except AttributeError:
                totals_dict = totals.dict()

            # Build provenance metadata
            provenance = {
                'source': source,
                'import_method': 'initial_dataset_load',
                'original_dataset': original_dataset,
                'strain_name': strain_name,
            }
            if 'sample_count' in strain_data:
                provenance['sample_count'] = strain_data['sample_count']

            profile = Profile(
                strain_normalized=normalized_name,
                terp_vector=terpenes,
                totals=totals_dict,
                category=category,
                provenance=provenance,
            )

            db.add(profile)
            imported_count += 1

            # Commit in batches
            if imported_count % batch_size == 0:
                db.commit()
                print(f"  Imported {imported_count:,} strains...")

        db.commit()
        print(f"  ✓ Successfully imported {imported_count:,} new strains")
        if skipped_count > 0:
            print(f"  → Skipped {skipped_count:,} existing/empty strains")

    except Exception as e:
        print(f"  ✗ Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return imported_count, skipped_count


# ---------------------------------------------------------------------------
# Main initialization flow
# ---------------------------------------------------------------------------

async def initialize_datasets():
    """Main initialization function - downloads and imports all datasets."""

    # Check if everything is already done
    all_done = all(is_dataset_initialized(key) for key in MARKERS)
    if all_done:
        print("✓ All datasets already initialized")
        return

    print("=" * 60)
    print("INITIALIZING STRAIN DATABASE WITH PUBLIC DATASETS")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # [1/4] Terpene Profile Parser
    # -----------------------------------------------------------------------
    if not is_dataset_initialized('terpene_parser'):
        try:
            print("\n[1/4] Terpene Profile Parser dataset...")
            csv_path = await download_file(TERPENE_PARSER_CSV, "terpene_parser.csv")
            strains = parse_terpene_parser_csv(csv_path)
            import_strains_to_db(strains, source='dataset_import', original_dataset='terpene_parser')
            mark_dataset_initialized('terpene_parser')
        except Exception as e:
            print(f"\n✗ Terpene Profile Parser import failed: {e}")
            print("  Continuing with other datasets...")
    else:
        print("\n[1/4] Terpene Profile Parser: already initialized ✓")

    # -----------------------------------------------------------------------
    # [2/4] Phytochemical Diversity
    # -----------------------------------------------------------------------
    if not is_dataset_initialized('phytochem'):
        try:
            print("\n[2/4] Phytochemical Diversity dataset...")
            csv_path = await download_file(
                PHYTOCHEM_CSV,
                "phytochem_diversity.csv",
                timeout=300.0,
                stream=True,
            )
            strains = parse_phytochem_csv(csv_path)
            import_strains_to_db(
                strains,
                source='dataset_phytochem',
                original_dataset='phytochem_diversity',
                batch_size=500,
            )
            mark_dataset_initialized('phytochem')
        except Exception as e:
            print(f"\n✗ Phytochemical Diversity import failed: {e}")
            print("  Continuing with other datasets...")
    else:
        print("\n[2/4] Phytochemical Diversity: already initialized ✓")

    # -----------------------------------------------------------------------
    # [3/4] OpenTHC Variety Database (name normalization only)
    # -----------------------------------------------------------------------
    if not is_dataset_initialized('openthc_varieties'):
        try:
            print("\n[3/4] OpenTHC Variety Database...")
            json_path = await download_file(OPENTHC_STRAINS_JSON, "openthc_strains.json")
            parse_openthc_varieties(json_path)
            mark_dataset_initialized('openthc_varieties')
        except Exception as e:
            print(f"\n✗ OpenTHC Variety import failed: {e}")
            print("  Continuing with other datasets...")
    else:
        print("\n[3/4] OpenTHC Varieties: already initialized ✓")

    # -----------------------------------------------------------------------
    # [4/4] Cannlytics Cannabis Results (state-by-state)
    # -----------------------------------------------------------------------
    if not is_dataset_initialized('cannlytics_results'):
        try:
            print("\n[4/4] Cannlytics Cannabis Results (state-by-state)...")
            total_imported = 0
            states_done = 0
            states_failed = []

            for state_code, state_name in CANNLYTICS_STATES:
                try:
                    url = f"{CANNLYTICS_BASE}/{state_code}/{state_code}-results-latest.csv"
                    filename = f"cannlytics_{state_code}.csv"

                    csv_path = await download_file(
                        url, filename, timeout=300.0, stream=True
                    )
                    strains = parse_cannlytics_state_csv(csv_path, state_name)

                    if strains:
                        imported, _ = import_strains_to_db(
                            strains,
                            source='dataset_cannlytics',
                            original_dataset=f'cannlytics_{state_code}',
                            batch_size=500,
                        )
                        total_imported += imported

                    states_done += 1

                except Exception as e:
                    print(f"  ⚠ Failed to import {state_name} ({state_code}): {e}")
                    states_failed.append(state_code)
                    continue

            print(f"\n  Cannlytics summary: {states_done}/{len(CANNLYTICS_STATES)} states imported")
            print(f"  Total new strains from Cannlytics: {total_imported:,}")
            if states_failed:
                print(f"  Failed states: {', '.join(states_failed)}")

            # Mark as initialized even if some states failed (partial success is fine)
            if states_done > 0:
                mark_dataset_initialized('cannlytics_results')

        except Exception as e:
            print(f"\n✗ Cannlytics Results import failed: {e}")
            print("  This dataset can be retried by deleting .initialized_cannlytics")
    else:
        print("\n[4/4] Cannlytics Results: already initialized ✓")

    print("\n" + "=" * 60)
    print("✓ DATASET INITIALIZATION COMPLETE")
    print("=" * 60)


def run_initialization():
    """Synchronous wrapper for async initialization."""
    asyncio.run(initialize_datasets())


if __name__ == "__main__":
    run_initialization()
