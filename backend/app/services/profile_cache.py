# Database caching service for strain terpene profiles
# Saves and retrieves strain data from PostgreSQL to avoid repeated API calls

from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import Profile
from app.db.base import SessionLocal
from app.models.schemas import Totals
from datetime import datetime


class ProfileCacheService:
    """Service for caching strain profiles in PostgreSQL."""

    def normalize_strain_name(self, name: str) -> str:
        """
        Normalize strain name for consistent lookups.

        Examples:
        - "Blue Dream" -> "blue dream"
        - "Girl Scout Cookies" -> "girl scout cookies"
        - "OG Kush #18" -> "og kush 18"
        """
        # Convert to lowercase
        name = name.lower()

        # Remove common suffixes
        suffixes = [
            'flower', 'bud', 'strain', 'cannabis',
            'indica', 'sativa', 'hybrid',
            'concentrate', 'extract', 'rosin'
        ]

        for suffix in suffixes:
            name = name.replace(f' {suffix}', '').replace(f'{suffix} ', '')

        # Clean special characters but keep spaces
        name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)

        # Normalize whitespace
        name = ' '.join(name.split())

        return name.strip()

    def get_cached_profile(self, strain_name: str) -> Optional[dict]:
        """
        Get cached strain profile from database.

        Args:
            strain_name: Raw strain name (will be normalized internally)

        Returns:
            Dict with terpenes, totals, category, or None if not found
        """
        normalized_name = self.normalize_strain_name(strain_name)

        db = SessionLocal()
        try:
            # Query for exact match on normalized name
            profile = db.query(Profile).filter(
                Profile.strain_normalized == normalized_name
            ).first()

            if profile:
                print(f"DEBUG: Found cached profile for '{strain_name}' (normalized: '{normalized_name}')")

                # Reconstruct Totals object from JSON
                totals_dict = profile.totals or {}
                totals = Totals(**totals_dict)

                return {
                    'terpenes': profile.terp_vector,
                    'totals': totals,
                    'category': profile.category,
                    'source': 'database',
                    'provenance': profile.provenance,
                    'cached_at': profile.created_at.isoformat() if profile.created_at else None
                }
            else:
                print(f"DEBUG: No cached profile found for '{strain_name}' (normalized: '{normalized_name}')")
                return None

        finally:
            db.close()

    def save_profile(
        self,
        strain_name: str,
        terpenes: dict,
        totals: Totals,
        category: str,
        source: str,
        extraction_id: Optional[int] = None
    ) -> bool:
        """
        Save strain profile to database.

        Args:
            strain_name: Raw strain name (will be normalized)
            terpenes: Dict of terpene name -> fraction value
            totals: Totals object with cannabinoid data
            category: SDP category (BLUE/YELLOW/etc)
            source: Where data came from ('api', 'coa', 'page')
            extraction_id: Optional link to extraction record

        Returns:
            True if saved successfully, False otherwise
        """
        normalized_name = self.normalize_strain_name(strain_name)

        db = SessionLocal()
        try:
            # Check if profile already exists
            existing = db.query(Profile).filter(
                Profile.strain_normalized == normalized_name
            ).first()

            if existing:
                print(f"DEBUG: Profile for '{strain_name}' already exists, updating...")

                # Update existing profile
                existing.terp_vector = terpenes
                existing.totals = totals.model_dump()
                existing.category = category
                existing.provenance = {
                    'source': source,
                    'updated_at': datetime.utcnow().isoformat(),
                    'original_name': strain_name
                }
                if extraction_id:
                    existing.extraction_id = extraction_id

            else:
                print(f"DEBUG: Creating new profile for '{strain_name}' (normalized: '{normalized_name}')")

                # Create new profile
                new_profile = Profile(
                    strain_normalized=normalized_name,
                    terp_vector=terpenes,
                    totals=totals.model_dump(),
                    category=category,
                    provenance={
                        'source': source,
                        'created_at': datetime.utcnow().isoformat(),
                        'original_name': strain_name
                    },
                    extraction_id=extraction_id
                )
                db.add(new_profile)

            db.commit()
            print(f"DEBUG: Successfully saved profile for '{strain_name}'")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save profile for '{strain_name}': {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_all_cached_strains(self, limit: int = 100) -> list[str]:
        """
        Get list of all cached strain names.
        Useful for fuzzy matching and autocomplete.

        Args:
            limit: Maximum number of strains to return

        Returns:
            List of normalized strain names
        """
        db = SessionLocal()
        try:
            profiles = db.query(Profile.strain_normalized).limit(limit).all()
            return [p.strain_normalized for p in profiles]
        finally:
            db.close()


# Global instance
profile_cache_service = ProfileCacheService()
