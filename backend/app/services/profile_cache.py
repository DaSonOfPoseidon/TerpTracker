# Database caching service for strain terpene profiles
# Saves and retrieves strain data from PostgreSQL to avoid repeated API calls

import json
import logging
import re
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import Profile
from app.db.base import SessionLocal
from app.models.schemas import Totals
from app.utils.normalization import normalize_strain_name as _normalize
from datetime import datetime

logger = logging.getLogger(__name__)

# Path to OpenTHC alias map (built during dataset init)
ALIAS_MAP_PATH = Path(__file__).parent.parent / "data" / "downloads" / "strain_alias_map.json"


class ProfileCacheService:
    """Service for caching strain profiles in PostgreSQL."""

    def normalize_strain_name(self, name: str) -> str:
        """Normalize strain name for consistent lookups (lowercase)."""
        return _normalize(name, title_case=False)

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
                logger.debug("Found cached profile for '%s' (normalized: '%s')", strain_name, normalized_name)

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
                logger.debug("No cached profile found for '%s' (normalized: '%s')", strain_name, normalized_name)
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
                logger.debug("Profile for '%s' already exists, updating...", strain_name)

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
                logger.debug("Creating new profile for '%s' (normalized: '%s')", strain_name, normalized_name)

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
            logger.debug("Successfully saved profile for '%s'", strain_name)
            return True

        except Exception as e:
            logger.error("Failed to save profile for '%s': %s", strain_name, e)
            db.rollback()
            return False
        finally:
            db.close()

    def _load_alias_map(self) -> dict:
        """Load OpenTHC stub -> canonical name alias map if available."""
        if not hasattr(self, '_alias_map'):
            self._alias_map = {}
            if ALIAS_MAP_PATH.exists():
                try:
                    with open(ALIAS_MAP_PATH, 'r', encoding='utf-8') as f:
                        self._alias_map = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
        return self._alias_map

    def _name_to_stub(self, name: str) -> str:
        """Convert a strain name to an OpenTHC-style stub for alias lookup."""
        stub = name.lower().strip()
        stub = re.sub(r'[^a-z0-9]', '', stub)
        return stub

    def resolve_strain_aliases(self, strain_name: str) -> list[str]:
        """
        Get alternative normalized names to try when a direct lookup fails.
        Uses the OpenTHC alias map (stub -> canonical name).
        """
        alias_map = self._load_alias_map()
        if not alias_map:
            return []

        stub = self._name_to_stub(strain_name)
        alternatives = []

        # Check if our stub matches a known strain
        if stub in alias_map:
            canonical = alias_map[stub]
            alt_normalized = self.normalize_strain_name(canonical)
            if alt_normalized != self.normalize_strain_name(strain_name):
                alternatives.append(alt_normalized)

        return alternatives

    def get_cached_profile_with_aliases(self, strain_name: str) -> Optional[dict]:
        """
        Get cached profile, falling back to alias lookup if direct match fails.
        """
        # Try direct lookup first
        result = self.get_cached_profile(strain_name)
        if result:
            return result

        # Try alias-based lookups
        for alt_name in self.resolve_strain_aliases(strain_name):
            db = SessionLocal()
            try:
                profile = db.query(Profile).filter(
                    Profile.strain_normalized == alt_name
                ).first()

                if profile:
                    logger.debug("Found profile via alias for '%s' -> '%s'", strain_name, alt_name)
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
            finally:
                db.close()

        return None

    def get_full_cached_result(self, strain_name: str) -> Optional[dict]:
        """
        Get a complete result dict for building an AnalyzeUrlResponse from cached data.
        Returns dict with strain_name, terpenes, totals, category, source, cached_at
        or None if not found.
        """
        cached = self.get_cached_profile_with_aliases(strain_name)
        if not cached:
            return None

        return {
            'strain_name': strain_name,
            'terpenes': cached.get('terpenes', {}),
            'totals': cached.get('totals', Totals()),
            'category': cached.get('category'),
            'source': 'database',
            'cached_at': cached.get('cached_at'),
        }

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

    def autocomplete_strains(self, query: str, limit: int = 10) -> list[dict]:
        """
        Fast prefix-only strain name search for autocomplete.
        Requires query length >= 2.

        Returns:
            List of {name, category} dicts
        """
        if len(query) < 2:
            return []

        normalized_query = self.normalize_strain_name(query)
        db = SessionLocal()
        try:
            profiles = db.query(Profile.strain_normalized, Profile.category).filter(
                Profile.strain_normalized.ilike(f"{normalized_query}%")
            ).limit(limit).all()

            return [
                {"name": p.strain_normalized, "category": p.category}
                for p in profiles
            ]
        finally:
            db.close()

    def search_strains(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search strains with prefix match first, then fuzzy matching.

        Returns:
            List of {name, category, match_score, match_type} dicts
        """
        if not query:
            return []

        normalized_query = self.normalize_strain_name(query)
        results = []
        seen_names = set()

        db = SessionLocal()
        try:
            # First: prefix matches via SQL ILIKE
            prefix_matches = db.query(Profile.strain_normalized, Profile.category).filter(
                Profile.strain_normalized.ilike(f"{normalized_query}%")
            ).limit(limit).all()

            for p in prefix_matches:
                results.append({
                    "name": p.strain_normalized,
                    "category": p.category,
                    "match_score": 1.0,
                    "match_type": "prefix",
                })
                seen_names.add(p.strain_normalized)

            # Second: fuzzy matches on remaining candidates if we have room
            if len(results) < limit:
                from rapidfuzz import process, fuzz

                # Get candidates not already matched
                all_names = db.query(Profile.strain_normalized, Profile.category).all()
                candidates = [(p.strain_normalized, p.category) for p in all_names if p.strain_normalized not in seen_names]

                if candidates:
                    candidate_names = [c[0] for c in candidates]
                    category_map = {c[0]: c[1] for c in candidates}

                    fuzzy_results = process.extract(
                        normalized_query,
                        candidate_names,
                        scorer=fuzz.ratio,
                        limit=limit - len(results),
                    )

                    for match_name, score, _ in fuzzy_results:
                        if score >= 60:  # minimum score threshold
                            results.append({
                                "name": match_name,
                                "category": category_map[match_name],
                                "match_score": round(score / 100, 2),
                                "match_type": "fuzzy",
                            })

            return results[:limit]
        finally:
            db.close()


# Global instance
profile_cache_service = ProfileCacheService()
