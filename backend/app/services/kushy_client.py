"""
Client for Kushy API - Free cannabis strain database
https://kushyapp.github.io/kushy-api-docs/public/
"""

import logging
import httpx
from typing import Optional
from app.models.schemas import StrainAPIData, Totals
from app.utils.conversions import safe_terpene_value

logger = logging.getLogger(__name__)


class KushyClient:
    """Client for interacting with Kushy API."""

    def __init__(self):
        self.base_url = "http://api.kushy.net/api/1.1/tables/strains/rows"

    async def get_strain_data(self, strain_name: str) -> Optional[StrainAPIData]:
        """
        Get strain terpene and cannabinoid data from Kushy API.

        Args:
            strain_name: Name of the strain to look up

        Returns:
            StrainAPIData with terpene profile, or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                logger.debug("Fetching strain data from Kushy API: %s", strain_name)

                # Kushy API doesn't have direct strain lookup by name
                # We need to fetch and filter (or use their search if available)
                # For now, try to get all strains and filter
                # Note: In production, you'd want to cache this or use better search
                response = await client.get(self.base_url)

                if response.status_code != 200:
                    logger.debug("Kushy API returned status %s", response.status_code)
                    return None

                result = response.json()
                logger.debug("Kushy API response type: %s", type(result))

                # Kushy returns an array of strain objects
                if not isinstance(result, list):
                    logger.debug("Kushy API did not return a list")
                    return None

                # Find strain by name (case-insensitive partial match)
                strain_lower = strain_name.lower()
                matching_strain = None

                for strain_obj in result:
                    if not isinstance(strain_obj, dict):
                        continue

                    strain_name_field = strain_obj.get('name', '')
                    if strain_name_field and strain_lower in strain_name_field.lower():
                        matching_strain = strain_obj
                        logger.debug("Found matching strain in Kushy: %s", strain_name_field)
                        break

                if not matching_strain:
                    logger.debug("No strain found in Kushy for '%s'", strain_name)
                    return None

                # Extract terpene and cannabinoid data
                terpenes = {}
                totals = Totals()

                # Kushy terpene field is a comma-separated string like "Limonene, Myrcene, Caryophyllene"
                # This gives us presence but not percentages
                terpene_str = matching_strain.get('terpenes', '')
                if terpene_str:
                    logger.debug("Kushy terpenes (qualitative): %s", terpene_str)
                    # Note: Kushy doesn't provide terpene percentages, just presence
                    # We can't return quantitative terpene data

                # Kushy cannabinoid fields (these appear to be percentages or presence)
                # Check if they provide actual values
                thc_val = matching_strain.get('thc')
                cbd_val = matching_strain.get('cbd')
                cbg_val = matching_strain.get('cbg')
                cbn_val = matching_strain.get('cbn')

                logger.debug("Kushy cannabinoids - THC: %s, CBD: %s, CBG: %s, CBN: %s", thc_val, cbd_val, cbg_val, cbn_val)

                # Parse cannabinoid values if present
                for raw_val, field in [(thc_val, 'thc'), (cbd_val, 'cbd'),
                                       (cbg_val, 'cbg'), (cbn_val, 'cbn')]:
                    parsed = safe_terpene_value(raw_val)
                    if parsed is not None:
                        setattr(totals, field, parsed)

                # Check if we got any useful data
                has_data = bool(terpenes) or any([
                    totals.thc, totals.cbd, totals.cbg, totals.cbn
                ])

                if not has_data:
                    logger.debug("Kushy strain found but no quantitative terpene/cannabinoid data")
                    return None

                return StrainAPIData(
                    strain_name=matching_strain.get('name', strain_name),
                    terpenes=terpenes,
                    totals=totals,
                    source='kushy',
                    match_score=0.9  # High confidence since we matched by name
                )

        except Exception as e:
            logger.error("Kushy API error", exc_info=True)
            return None


# Global instance
kushy_client = KushyClient()
