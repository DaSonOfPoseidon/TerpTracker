"""
Client for Otreeba (Open Cannabis API)
https://api.otreeba.com/swagger/
"""

import httpx
from typing import Optional
from app.core.config import settings
from app.models.schemas import StrainAPIData, Totals


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
            print("Otreeba API key not configured")
            return None

        try:
            import urllib.parse

            encoded_name = urllib.parse.quote_plus(strain_name)

            async with httpx.AsyncClient(timeout=15.0) as client:
                # Otreeba requires API key in header
                headers = {
                    "X-API-Key": self.api_key,
                    "Accept": "application/json"
                }

                # Try strains endpoint
                url = f"{self.base_url}/strains"
                print(f"Fetching strain data from Otreeba API: {strain_name}")

                # Search for strain by name
                response = await client.get(
                    url,
                    headers=headers,
                    params={"q": strain_name, "count": 10}
                )

                if response.status_code != 200:
                    print(f"Otreeba API returned status {response.status_code}")
                    return None

                result = response.json()
                print(f"Otreeba API response type: {type(result)}")

                # Otreeba typically returns {"data": [...]}
                data = result.get('data', [])
                if not data or not isinstance(data, list):
                    print("No strains found in Otreeba response")
                    return None

                # Find best match (first result should be closest)
                strain = data[0]
                print(f"Found strain in Otreeba: {strain.get('name')}")

                # Extract terpene and cannabinoid data
                terpenes = {}
                totals = Totals()

                # Otreeba structure varies - check for lab results
                # Common fields: thc, cbd, labResults, etc.
                if 'thc' in strain:
                    try:
                        val = float(strain['thc'])
                        totals.thc = val / 100 if val > 1 else val
                    except (ValueError, TypeError):
                        pass

                if 'cbd' in strain:
                    try:
                        val = float(strain['cbd'])
                        totals.cbd = val / 100 if val > 1 else val
                    except (ValueError, TypeError):
                        pass

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
                                value = analyte.get('value')

                                if value is None:
                                    continue

                                try:
                                    val = float(value)

                                    # Map terpenes
                                    if 'myrcene' in name:
                                        terpenes['myrcene'] = val / 100 if val > 1 else val
                                    elif 'limonene' in name:
                                        terpenes['limonene'] = val / 100 if val > 1 else val
                                    elif 'caryophyllene' in name:
                                        terpenes['caryophyllene'] = val / 100 if val > 1 else val
                                    elif 'pinene' in name:
                                        if 'alpha' in name:
                                            terpenes['alpha_pinene'] = val / 100 if val > 1 else val
                                        elif 'beta' in name:
                                            terpenes['beta_pinene'] = val / 100 if val > 1 else val
                                    elif 'terpinolene' in name:
                                        terpenes['terpinolene'] = val / 100 if val > 1 else val
                                    elif 'humulene' in name:
                                        terpenes['humulene'] = val / 100 if val > 1 else val
                                    elif 'linalool' in name:
                                        terpenes['linalool'] = val / 100 if val > 1 else val
                                    elif 'ocimene' in name:
                                        terpenes['ocimene'] = val / 100 if val > 1 else val

                                    # Map cannabinoids
                                    elif name == 'thc' or 'delta-9' in name:
                                        totals.thc = val / 100 if val > 1 else val
                                    elif name == 'thca':
                                        totals.thca = val / 100 if val > 1 else val
                                    elif name == 'cbd':
                                        totals.cbd = val / 100 if val > 1 else val
                                    elif name == 'cbda':
                                        totals.cbda = val / 100 if val > 1 else val
                                    elif name == 'cbn':
                                        totals.cbn = val / 100 if val > 1 else val
                                    elif name == 'cbg':
                                        totals.cbg = val / 100 if val > 1 else val
                                except (ValueError, TypeError):
                                    pass

                # Check if we got any useful data
                has_data = bool(terpenes) or any([
                    totals.thc, totals.cbd, totals.thca, totals.cbda,
                    totals.cbn, totals.cbg
                ])

                if not has_data:
                    print("Otreeba strain found but no terpene/cannabinoid data")
                    return None

                print(f"Otreeba data - Terpenes: {len(terpenes)}, Cannabinoids: {bool(totals.thc or totals.cbd)}")

                return StrainAPIData(
                    strain_name=strain.get('name', strain_name),
                    terpenes=terpenes,
                    totals=totals,
                    source='otreeba',
                    match_score=0.85  # Good confidence from professional API
                )

        except Exception as e:
            print(f"Otreeba API error: {e}")
            return None


# Global instance
otreeba_client = OtreebaClient()
