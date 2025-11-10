"""
Main analyzer service that coordinates the extraction pipeline:
1. Scrape page
2. Parse COA if found
3. Fallback to strain APIs with fuzzy matching
4. Classify and generate summary
"""

from typing import Dict
from rapidfuzz import fuzz, process
from app.models.schemas import AnalyzeUrlResponse, Evidence, Totals
from app.services.scraper import scrape_url
from app.services.cannlytics_client import CannlyticsClient
from app.services.classifier import classify_terpene_profile, generate_summary

class StrainAnalyzer:
    """Main service for analyzing strain URLs and extracting terpene profiles."""

    def __init__(self):
        self.cannlytics = CannlyticsClient()

    async def analyze_url(self, url: str) -> AnalyzeUrlResponse:
        """
        Analyze a URL and return terpene profile with SDP classification.

        Pipeline:
        1. Scrape the page with Playwright
        2. If terpenes found on page → use them
        3. Else if COA link found → parse COA
        4. Else → fuzzy match strain name and query API
        5. Classify into SDP category
        6. Generate friendly summary

        Args:
            url: URL to analyze

        Returns:
            AnalyzeUrlResponse with complete analysis
        """
        # Step 1: Scrape the page
        scraped = await scrape_url(url)

        source = "page"
        terpenes = scraped.terpenes
        totals = scraped.totals
        strain_name = scraped.strain_name or "Unknown Strain"
        evidence_data = {
            "detection_method": "page_scrape",
            "url": url
        }

        # Step 2: If no terpenes on page, try COA links
        if not terpenes and scraped.coa_links:
            for coa_url in scraped.coa_links:
                coa_data = await self.cannlytics.parse_coa(coa_url)
                if coa_data and coa_data.terpenes:
                    source = "coa"
                    terpenes = coa_data.terpenes
                    totals = coa_data.totals
                    if coa_data.strain_name:
                        strain_name = coa_data.strain_name

                    evidence_data = {
                        "detection_method": "coa_parse",
                        "url": url,
                        "coa_url": coa_url,
                        "coa_lab": coa_data.lab_name,
                        "coa_date": coa_data.test_date
                    }
                    break  # Use first successful COA

        # Step 3: If still no terpenes, try strain API fallback with fuzzy matching
        if not terpenes and strain_name:
            # Try exact match first
            strain_data = await self.cannlytics.get_strain_data(strain_name)

            # If no exact match, try fuzzy matching
            # (In production, you'd maintain a cache of known strain names)
            if not strain_data:
                # For now, just try the API with the name as-is
                # A full implementation would fuzzy match against a strain database
                normalized_name = self.normalize_strain_name(strain_name)
                strain_data = await self.cannlytics.get_strain_data(normalized_name)

            if strain_data and strain_data.terpenes:
                source = "api"
                terpenes = strain_data.terpenes
                strain_name = strain_data.strain_name

                evidence_data = {
                    "detection_method": "api_fallback",
                    "url": url,
                    "api_source": strain_data.source,
                    "match_score": strain_data.match_score
                }

        # If we still have no terpenes, return error
        if not terpenes:
            raise ValueError("Could not extract terpene data from any source")

        # Step 4: Classify into SDP category
        category = classify_terpene_profile(terpenes)

        # Step 5: Generate friendly summary
        summary = generate_summary(strain_name, category, terpenes)

        # Build response
        return AnalyzeUrlResponse(
            source=source,
            terpenes=terpenes,
            totals=totals.model_dump(),
            category=category,
            summary=summary,
            strain_guess=strain_name,
            evidence=Evidence(**evidence_data)
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
