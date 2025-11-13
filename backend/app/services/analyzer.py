"""
Main analyzer service that coordinates the extraction pipeline:
1. Scrape page
2. Parse COA if found
3. Check database cache for strain profile
4. Fallback to strain APIs with fuzzy matching (Cannlytics → Kushy → Otreeba*)
5. Save API results to database
6. Classify and generate summary

*Otreeba currently disabled - enable in config when ready
"""

from typing import Dict, List
from rapidfuzz import fuzz, process
from app.models.schemas import AnalyzeUrlResponse, Evidence, Totals, DataAvailability
from app.services.scraper import scrape_url
from app.services.cannlytics_client import CannlyticsClient
from app.services.kushy_client import kushy_client
# from app.services.otreeba_client import otreeba_client  # Disabled until costs reviewed
from app.services.classifier import classify_terpene_profile, generate_summary, generate_cannabinoid_insights
from app.services.profile_cache import profile_cache_service

class StrainAnalyzer:
    """Main service for analyzing strain URLs and extracting terpene profiles."""

    def __init__(self):
        self.cannlytics = CannlyticsClient()

    def is_data_complete(self, terpenes: Dict[str, float], totals: Totals) -> bool:
        """
        Check if we have enough data to skip API supplementation.

        Returns True if:
        - We have 5+ terpenes AND
        - We have at least one major cannabinoid (THC/CBD/CBG/CBN)
        """
        has_enough_terpenes = len(terpenes) >= 5
        has_major_cannabinoids = any([totals.thc, totals.thca, totals.cbd, totals.cbda, totals.cbn, totals.cbg])
        return has_enough_terpenes and has_major_cannabinoids

    def merge_terpene_data(self,
                          coa_terpenes: Dict[str, float],
                          page_terpenes: Dict[str, float],
                          db_terpenes: Dict[str, float],
                          api_terpenes: Dict[str, float]) -> tuple[Dict[str, float], List[str]]:
        """
        Merge terpene data from multiple sources with priority: COA > Page > Database > API.

        For each terpene compound:
        - Use highest priority source that has it
        - Conflicts are resolved by using priority source

        Returns:
            Tuple of (merged_terpenes, sources_used)
        """
        merged = {}
        sources_used = set()

        # Priority order: COA, Page, Database, API
        sources = [
            ('coa', coa_terpenes),
            ('page', page_terpenes),
            ('database', db_terpenes),
            ('api', api_terpenes)
        ]

        # Collect all unique terpene keys
        all_keys = set()
        for _, terp_data in sources:
            if terp_data:
                all_keys.update(terp_data.keys())

        # For each terpene, use highest priority source
        for key in all_keys:
            for source_name, terp_data in sources:
                if terp_data and key in terp_data and terp_data[key] is not None and terp_data[key] > 0:
                    merged[key] = terp_data[key]
                    sources_used.add(source_name)
                    break  # Use first (highest priority) source that has this terpene

        return merged, list(sources_used)

    def merge_cannabinoid_data(self,
                               coa_totals: Totals,
                               page_totals: Totals,
                               db_totals: Totals,
                               api_totals: Totals) -> tuple[Totals, List[str]]:
        """
        Merge cannabinoid data from multiple sources with priority: COA > Page > Database > API.

        For each cannabinoid field:
        - Use highest priority source that has it
        - Conflicts are resolved by using priority source

        Returns:
            Tuple of (merged_totals, sources_used)
        """
        merged = Totals()
        sources_used = set()

        # Priority order
        sources = [
            ('coa', coa_totals),
            ('page', page_totals),
            ('database', db_totals),
            ('api', api_totals)
        ]

        # All cannabinoid fields in Totals model
        cannabinoid_fields = [
            'total_terpenes', 'thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
            'cbn', 'cbg', 'cbgm', 'cbgv', 'cbc', 'cbcv', 'cbv', 'cbe', 'cbt', 'cbl'
        ]

        # For each field, use highest priority source
        for field in cannabinoid_fields:
            for source_name, totals_obj in sources:
                if totals_obj:
                    value = getattr(totals_obj, field, None)
                    if value is not None and value > 0:
                        setattr(merged, field, value)
                        sources_used.add(source_name)
                        break  # Use first (highest priority) source that has this field

        return merged, list(sources_used)

    async def analyze_url(self, url: str) -> AnalyzeUrlResponse:
        """
        Analyze a URL and return terpene profile with SDP classification.

        NEW Pipeline (Multi-Source Merging):
        1. Scrape the page with Playwright
        2. Try COA links if found (always attempt)
        3. Always check database cache for supplemental data
        4. Conditionally query APIs if data incomplete (<5 terpenes or missing major cannabinoids)
        5. Merge all collected data with priority: COA > Page > Database > API
        6. Classify and generate summary from merged data

        Args:
            url: URL to analyze

        Returns:
            AnalyzeUrlResponse with merged multi-source analysis
        """
        # Step 1: Scrape the page
        print(f"DEBUG: Scraping page...")
        scraped = await scrape_url(url)
        strain_name = scraped.strain_name or "Unknown Strain"

        # Initialize data containers for each source
        page_terpenes = scraped.terpenes
        page_totals = scraped.totals
        coa_terpenes = {}
        coa_totals = Totals()
        db_terpenes = {}
        db_totals = Totals()
        api_terpenes = {}
        api_totals = Totals()

        # Evidence tracking
        coa_url = None
        coa_lab = None
        coa_date = None
        api_source = None
        cached_at = None

        # Step 2: Try COA links if found (always attempt, regardless of page data)
        if scraped.coa_links:
            print(f"DEBUG: Found {len(scraped.coa_links)} COA link(s), attempting to parse...")
            for coa_link in scraped.coa_links:
                coa_data = await self.cannlytics.parse_coa(coa_link)
                if coa_data and coa_data.terpenes:
                    print(f"DEBUG: Successfully parsed COA from {coa_link}")
                    coa_terpenes = coa_data.terpenes
                    coa_totals = coa_data.totals
                    coa_url = coa_link
                    coa_lab = coa_data.lab_name
                    coa_date = coa_data.test_date
                    if coa_data.strain_name:
                        strain_name = coa_data.strain_name
                    break  # Use first successful COA

        # Step 3: Always check database cache for supplemental data
        if strain_name:
            print(f"DEBUG: Checking database for '{strain_name}'...")
            cached_profile = profile_cache_service.get_cached_profile(strain_name)
            if cached_profile:
                print(f"DEBUG: Found cached profile for '{strain_name}'")
                if cached_profile['terpenes']:
                    db_terpenes = cached_profile['terpenes']
                if cached_profile['totals']:
                    db_totals = cached_profile['totals']
                cached_at = cached_profile.get('cached_at')

        # Step 4: Check if we need API supplementation
        # Collect current terpenes/totals from page + COA + database
        preliminary_terpenes, _ = self.merge_terpene_data(coa_terpenes, page_terpenes, db_terpenes, {})
        preliminary_totals, _ = self.merge_cannabinoid_data(coa_totals, page_totals, db_totals, Totals())

        # Conditionally query APIs if data incomplete
        if not self.is_data_complete(preliminary_terpenes, preliminary_totals):
            print(f"DEBUG: Data incomplete (terpenes: {len(preliminary_terpenes)}, need 5+), querying APIs...")

            # Try Cannlytics first (exact match)
            print(f"DEBUG: Trying Cannlytics API...")
            strain_data = await self.cannlytics.get_strain_data(strain_name)

            # If no exact match, try Cannlytics with fuzzy matching
            if not strain_data:
                normalized_name = self.normalize_strain_name(strain_name)
                print(f"DEBUG: Trying Cannlytics API with normalized name: '{normalized_name}'")
                strain_data = await self.cannlytics.get_strain_data(normalized_name)

            # If Cannlytics fails, try Kushy API
            if not strain_data:
                print(f"DEBUG: Cannlytics returned no data, trying Kushy API...")
                strain_data = await kushy_client.get_strain_data(strain_name)

            # If Kushy fails, try Kushy with normalized name
            if not strain_data:
                normalized_name = self.normalize_strain_name(strain_name)
                print(f"DEBUG: Trying Kushy API with normalized name: '{normalized_name}'")
                strain_data = await kushy_client.get_strain_data(normalized_name)

            # Future: Add Otreeba here when enabled
            # if not strain_data and settings.otreeba_enabled:
            #     print(f"DEBUG: Kushy returned no data, trying Otreeba API...")
            #     strain_data = await otreeba_client.get_strain_data(strain_name)

            if strain_data:
                print(f"DEBUG: Got data from API: {strain_data.source}")
                if strain_data.terpenes:
                    api_terpenes = strain_data.terpenes
                if strain_data.totals:
                    api_totals = strain_data.totals
                api_source = strain_data.source
                strain_name = strain_data.strain_name
        else:
            print(f"DEBUG: Data complete (terpenes: {len(preliminary_terpenes)}), skipping API calls")

        # Step 5: Merge all data sources with priority rules
        print(f"DEBUG: Merging data from all sources...")
        merged_terpenes, terp_sources = self.merge_terpene_data(coa_terpenes, page_terpenes, db_terpenes, api_terpenes)
        merged_totals, cannabinoid_sources = self.merge_cannabinoid_data(coa_totals, page_totals, db_totals, api_totals)

        # Combine sources used (maintain order)
        all_sources = []
        if 'coa' in terp_sources or 'coa' in cannabinoid_sources:
            all_sources.append('coa')
        if 'page' in terp_sources or 'page' in cannabinoid_sources:
            all_sources.append('page')
        if 'database' in terp_sources or 'database' in cannabinoid_sources:
            all_sources.append('database')
        if 'api' in terp_sources or 'api' in cannabinoid_sources:
            all_sources.append('api')

        # If no sources, set default to page (we at least tried scraping)
        if not all_sources:
            all_sources = ['page']

        print(f"DEBUG: Final merged data - Terpenes: {len(merged_terpenes)}, Sources: {all_sources}")

        # Calculate data availability
        has_terpenes = bool(merged_terpenes)
        has_cannabinoids = any([merged_totals.thc, merged_totals.thca, merged_totals.cbd, merged_totals.cbda,
                                merged_totals.cbn, merged_totals.cbg, merged_totals.cbc])
        has_coa = 'coa' in all_sources

        # Require at least SOME data
        if not has_terpenes and not has_cannabinoids:
            raise ValueError("Could not extract terpene or cannabinoid data from any source")

        # Step 6: Classify into SDP category (only if we have terpenes)
        category = None
        if has_terpenes:
            category = classify_terpene_profile(merged_terpenes)
            print(f"DEBUG: Classified as {category}")

        # Step 7: Save merged results to database for future lookups
        # Save if we have valid data from page/COA (not just from database/API)
        if ('page' in all_sources or 'coa' in all_sources) and merged_terpenes and category and strain_name:
            primary_source = 'coa' if 'coa' in all_sources else 'page'
            print(f"DEBUG: Saving merged result to database for '{strain_name}' (primary source: {primary_source})")
            profile_cache_service.save_profile(
                strain_name=strain_name,
                terpenes=merged_terpenes,
                totals=merged_totals,
                category=category,
                source=primary_source
            )

        # Step 8: Generate summary
        if has_terpenes and category:
            summary = generate_summary(strain_name, category, merged_terpenes)
        elif has_cannabinoids:
            # Cannabinoid-only summary
            summary = f"{strain_name} - Cannabinoid data available"
        else:
            summary = f"{strain_name} - Limited data available"

        # Step 9: Generate cannabinoid insights
        cannabinoid_insights = []
        if has_cannabinoids:
            cannabinoid_insights = generate_cannabinoid_insights(merged_totals)

        # Step 10: Build evidence object
        # Determine primary detection method
        if 'coa' in all_sources:
            primary_method = "coa_parse"
        elif 'page' in all_sources:
            primary_method = "page_scrape"
        elif 'database' in all_sources:
            primary_method = "database_cache"
        else:
            primary_method = "api_fallback"

        evidence_data = {
            "detection_method": primary_method,
            "url": url
        }
        if coa_url:
            evidence_data["coa_url"] = coa_url
            evidence_data["coa_lab"] = coa_lab
            evidence_data["coa_date"] = coa_date
        if api_source:
            evidence_data["api_source"] = api_source
        if cached_at:
            evidence_data["cached_at"] = cached_at

        # Build data availability object
        data_available = DataAvailability(
            has_terpenes=has_terpenes,
            has_cannabinoids=has_cannabinoids,
            has_coa=has_coa,
            terpene_count=len(merged_terpenes) if merged_terpenes else 0,
            cannabinoid_count=sum(1 for field in ['thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
                                                    'cbn', 'cbg', 'cbc', 'cbcv']
                                  if getattr(merged_totals, field, None))
        )

        # Build response
        return AnalyzeUrlResponse(
            sources=all_sources,  # NEW: List of sources used
            terpenes=merged_terpenes or {},
            totals=merged_totals,
            category=category,
            summary=summary,
            strain_guess=strain_name,
            evidence=Evidence(**evidence_data),
            data_available=data_available,
            cannabinoid_insights=cannabinoid_insights
        )

    def normalize_strain_name(self, name: str) -> str:
        """
        Normalize strain name for better API matching.

        Removes common suffixes, cleans special characters, etc.
        """
        # Remove common product type suffixes
        name = name.lower()
        suffixes = [
            'flower', 'bud', 'strain', 'cannabis',
            'indica', 'sativa', 'hybrid',
            'concentrate', 'extract', 'rosin'
        ]

        for suffix in suffixes:
            name = name.replace(f' {suffix}', '').replace(f'{suffix} ', '')

        # Clean special characters
        name = ''.join(c for c in name if c.isalnum() or c.isspace())
        name = ' '.join(name.split())  # Normalize whitespace

        return name.strip().title()

    def fuzzy_match_strain(self, query: str, candidates: list[str], threshold: float = 0.8) -> tuple[str, float]:
        """
        Fuzzy match a strain name against a list of candidates.

        Args:
            query: The strain name to match
            candidates: List of known strain names
            threshold: Minimum match score (0-1)

        Returns:
            Tuple of (best_match, score) or (query, 0.0) if no good match
        """
        if not candidates:
            return query, 0.0

        # Use RapidFuzz to find best match
        result = process.extractOne(
            query,
            candidates,
            scorer=fuzz.ratio
        )

        if result and result[1] >= threshold * 100:  # RapidFuzz returns 0-100
            return result[0], result[1] / 100
        else:
            return query, 0.0
