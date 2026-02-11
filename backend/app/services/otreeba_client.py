"""
Client for Otreeba (Open Cannabis API)
https://api.otreeba.com/swagger/
"""

import logging
import urllib.parse
import httpx
from typing import Optional
from app.core.config import settings
from app.models.schemas import StrainAPIData, Totals
from app.utils.conversions import safe_terpene_value

logger = logging.getLogger(__name__)


class OtreebaClient:
    """Client for interacting with Otreeba API."""

    def __init__(self):
        self.base_url = "https://api.otreeba.com/v1"
        self.api_key = settings.otreeba_api_key

    async def get_strain_data(self, strain_name: str) -> Optional[StrainAPIData]:
        """
        Get strain terpene and cannabinoid data from Otreeba API.

        Args:
            strain_name: Name of the strain to look up

        Returns:
            StrainAPIData with terpene profile, or None if not found
        """
        if not self.api_key:
            logger.debug("Otreeba API key not configured")
            return None

        try:
            encoded_name = urllib.parse.quote_plus(strain_name)

            async with httpx.AsyncClient(timeout=15.0) as client:
                # Otreeba requires API key in header
                headers = {
                    "X-API-Key": self.api_key,
                    "Accept": "application/json"
                }

                # Try strains endpoint
                url = f"{self.base_url}/strains"
                logger.debug("Fetching strain data from Otreeba API: %s", strain_name)

                # Search for strain by name
                response = await client.get(
                    url,
                    headers=headers,
                    params={"q": strain_name, "count": 10}
                )

                if response.status_code != 200:
                    logger.debug("Otreeba API returned status %s", response.status_code)
                    return None

                result = response.json()
                logger.debug("Otreeba API response type: %s", type(result))

                # Otreeba typically returns {"data": [...]}
                data = result.get('data', [])
                if not data or not isinstance(data, list):
                    logger.debug("No strains found in Otreeba response")
                    return None

                # Find best match (first result should be closest)
                strain = data[0]
                logger.debug("Found strain in Otreeba: %s", strain.get('name'))

                # Extract terpene and cannabinoid data
                terpenes = {}
                totals = Totals()

                # Otreeba structure varies - check for lab results
                # Common fields: thc, cbd, labResults, etc.
                for field in ['thc', 'cbd']:
                    if field in strain:
                        val = safe_terpene_value(strain[field])
                        if val is not None:
                            setattr(totals, field, val)

                # Check for lab results which might have more detailed data
                lab_results = strain.get('labResults', [])
                if lab_results and isinstance(lab_results, list):
                    for result in lab_results:
                        if not isinstance(result, dict):
                            continue

                        # Look for terpene and cannabinoid data in lab results
                        analytes = result.get('analytes', [])
                        if analytes:
                            for analyte in analytes:
                                if not isinstance(analyte, dict):
                                    continue

                                name = analyte.get('name', '').lower()
                                raw_value = analyte.get('value')
                                if raw_value is None:
                                    continue

                                val = safe_terpene_value(raw_value)
                                if val is None:
                                    continue

                                # Map terpenes
                                terpene_map = {
                                    'myrcene': 'myrcene', 'limonene': 'limonene',
                                    'caryophyllene': 'caryophyllene', 'terpinolene': 'terpinolene',
                                    'humulene': 'humulene', 'linalool': 'linalool', 'ocimene': 'ocimene',
                                }
                                cannabinoid_map = {
                                    'thca': 'thca', 'cbd': 'cbd', 'cbda': 'cbda',
                                    'cbn': 'cbn', 'cbg': 'cbg',
                                }
                                matched = False
                                for keyword, std in terpene_map.items():
                                    if keyword in name:
                                        if keyword == 'pinene':
                                            continue  # handled below
                                        terpenes[std] = val
                                        matched = True
                                        break
                                if not matched and 'pinene' in name:
                                    if 'alpha' in name:
                                        terpenes['alpha_pinene'] = val
                                    elif 'beta' in name:
                                        terpenes['beta_pinene'] = val
                                    matched = True
                                if not matched:
                                    if name == 'thc' or 'delta-9' in name:
                                        totals.thc = val
                                    else:
                                        for keyword, std in cannabinoid_map.items():
                                            if name == keyword:
                                                setattr(totals, std, val)
                                                break

                # Check if we got any useful data
                has_data = bool(terpenes) or any([
                    totals.thc, totals.cbd, totals.thca, totals.cbda,
                    totals.cbn, totals.cbg
                ])

                if not has_data:
                    logger.debug("Otreeba strain found but no terpene/cannabinoid data")
                    return None

                logger.info("Otreeba data - Terpenes: %s, Cannabinoids: %s", len(terpenes), bool(totals.thc or totals.cbd))

                return StrainAPIData(
                    strain_name=strain.get('name', strain_name),
                    terpenes=terpenes,
                    totals=totals,
                    source='otreeba',
                    match_score=0.85  # Good confidence from professional API
                )

        except Exception as e:
            logger.error("Otreeba API error", exc_info=True)
            return None


# Global instance
otreeba_client = OtreebaClient()
