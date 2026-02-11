"""
Main analyzer service that coordinates the extraction pipeline:
1. Scrape page
2. Parse COA if found
3. Check database cache for strain profile
4. Fallback to strain APIs with fuzzy matching (Cannlytics -> Kushy -> Otreeba*)
5. Save API results to database
6. Classify and generate summary

*Otreeba currently disabled - enable in config when ready
"""

import logging
from typing import Dict, List
from app.core.constants import MIN_TERPENES_FOR_COMPLETE
from app.models.schemas import AnalyzeUrlResponse, Evidence, Totals, DataAvailability
from app.services.scraper import scrape_url
from app.services.cannlytics_client import CannlyticsClient
from app.services.kushy_client import kushy_client
from app.services.classifier import classify_terpene_profile, generate_summary, generate_cannabinoid_insights
from app.services.profile_cache import profile_cache_service
from app.utils.normalization import normalize_strain_name
from app.utils.merging import merge_terpene_data, merge_cannabinoid_data
from app.utils.matching import fuzzy_match_strain

logger = logging.getLogger(__name__)


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
        has_enough_terpenes = len(terpenes) >= MIN_TERPENES_FOR_COMPLETE
        has_major_cannabinoids = any([totals.thc, totals.thca, totals.cbd, totals.cbda, totals.cbn, totals.cbg])
        return has_enough_terpenes and has_major_cannabinoids

    async def analyze_url(self, url: str) -> AnalyzeUrlResponse:
        """
        Analyze a URL and return terpene profile with SDP classification.

        Pipeline:
        1. Scrape the page with Playwright
        2. Try COA links if found (always attempt)
        3. Always check database cache for supplemental data
        4. Conditionally query APIs if data incomplete
        5. Merge all collected data with priority: COA > Page > Database > API
        6. Classify and generate summary from merged data
        """
        # Step 1: Scrape the page
        logger.debug("Scraping page...")
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
            logger.debug("Found %d COA link(s), attempting to parse...", len(scraped.coa_links))
            for coa_link in scraped.coa_links:
                coa_data = await self.cannlytics.parse_coa(coa_link)
                if coa_data and coa_data.terpenes:
                    logger.debug("Successfully parsed COA from %s", coa_link)
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
            logger.debug("Checking database for '%s'...", strain_name)
            cached_profile = profile_cache_service.get_cached_profile(strain_name)
            if cached_profile:
                logger.debug("Found cached profile for '%s'", strain_name)
                if cached_profile['terpenes']:
                    db_terpenes = cached_profile['terpenes']
                if cached_profile['totals']:
                    db_totals = cached_profile['totals']
                cached_at = cached_profile.get('cached_at')

        # Step 4: Check if we need API supplementation
        preliminary_terpenes, _ = merge_terpene_data(coa_terpenes, page_terpenes, db_terpenes, {})
        preliminary_totals, _ = merge_cannabinoid_data(coa_totals, page_totals, db_totals, Totals())

        if not self.is_data_complete(preliminary_terpenes, preliminary_totals):
            logger.debug("Data incomplete (terpenes: %d, need %d+), querying APIs...", len(preliminary_terpenes), MIN_TERPENES_FOR_COMPLETE)

            # Try Cannlytics first (exact match)
            logger.debug("Trying Cannlytics API...")
            strain_data = await self.cannlytics.get_strain_data(strain_name)

            # If no exact match, try with normalized name
            if not strain_data:
                normalized_name = normalize_strain_name(strain_name, title_case=True)
                logger.debug("Trying Cannlytics API with normalized name: '%s'", normalized_name)
                strain_data = await self.cannlytics.get_strain_data(normalized_name)

            # If Cannlytics fails, try Kushy API
            if not strain_data:
                logger.debug("Cannlytics returned no data, trying Kushy API...")
                strain_data = await kushy_client.get_strain_data(strain_name)

            # If Kushy fails, try Kushy with normalized name
            if not strain_data:
                normalized_name = normalize_strain_name(strain_name, title_case=True)
                logger.debug("Trying Kushy API with normalized name: '%s'", normalized_name)
                strain_data = await kushy_client.get_strain_data(normalized_name)

            if strain_data:
                logger.debug("Got data from API: %s", strain_data.source)
                if strain_data.terpenes:
                    api_terpenes = strain_data.terpenes
                if strain_data.totals:
                    api_totals = strain_data.totals
                api_source = strain_data.source
                strain_name = strain_data.strain_name
        else:
            logger.debug("Data complete (terpenes: %d), skipping API calls", len(preliminary_terpenes))

        # Step 5: Merge all data sources with priority rules
        logger.debug("Merging data from all sources...")
        merged_terpenes, terp_sources = merge_terpene_data(coa_terpenes, page_terpenes, db_terpenes, api_terpenes)
        merged_totals, cannabinoid_sources = merge_cannabinoid_data(coa_totals, page_totals, db_totals, api_totals)

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

        if not all_sources:
            all_sources = ['page']

        logger.debug("Final merged data - Terpenes: %d, Sources: %s", len(merged_terpenes), all_sources)

        # Calculate data availability
        has_terpenes = bool(merged_terpenes)
        has_cannabinoids = any([merged_totals.thc, merged_totals.thca, merged_totals.cbd, merged_totals.cbda,
                                merged_totals.cbn, merged_totals.cbg, merged_totals.cbc])
        has_coa = 'coa' in all_sources

        if not has_terpenes and not has_cannabinoids:
            raise ValueError("Could not extract terpene or cannabinoid data from any source")

        # Step 6: Classify into SDP category (only if we have terpenes)
        category = None
        if has_terpenes:
            category = classify_terpene_profile(merged_terpenes)
            logger.debug("Classified as %s", category)

        # Step 7: Save merged results to database for future lookups
        if ('page' in all_sources or 'coa' in all_sources) and merged_terpenes and category and strain_name:
            primary_source = 'coa' if 'coa' in all_sources else 'page'
            logger.debug("Saving merged result to database for '%s' (primary source: %s)", strain_name, primary_source)
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
            summary = f"{strain_name} - Cannabinoid data available"
        else:
            summary = f"{strain_name} - Limited data available"

        # Step 9: Generate cannabinoid insights
        cannabinoid_insights = []
        if has_cannabinoids:
            cannabinoid_insights = generate_cannabinoid_insights(merged_totals)

        # Step 10: Build evidence object
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

        data_available = DataAvailability(
            has_terpenes=has_terpenes,
            has_cannabinoids=has_cannabinoids,
            has_coa=has_coa,
            terpene_count=len(merged_terpenes) if merged_terpenes else 0,
            cannabinoid_count=sum(1 for field in ['thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
                                                    'cbn', 'cbg', 'cbc', 'cbcv']
                                  if getattr(merged_totals, field, None))
        )

        return AnalyzeUrlResponse(
            sources=all_sources,
            terpenes=merged_terpenes or {},
            totals=merged_totals,
            category=category,
            summary=summary,
            strain_guess=strain_name,
            evidence=Evidence(**evidence_data),
            data_available=data_available,
            cannabinoid_insights=cannabinoid_insights
        )
