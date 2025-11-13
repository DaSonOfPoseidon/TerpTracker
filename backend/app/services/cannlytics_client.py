"""
Client for Cannlytics API:
- COA Data Extraction API for parsing certificates of analysis
- Strain Data API for fallback strain information
"""

import httpx
from typing import Optional, Dict, List
from app.core.config import settings
from app.models.schemas import COAData, StrainAPIData, Totals

class CannlyticsClient:
    """Client for interacting with Cannlytics APIs."""

    def __init__(self):
        self.base_url = settings.cannlytics_base_url
        self.api_key = settings.cannlytics_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def parse_coa(self, coa_url: str) -> Optional[COAData]:
        """
        Parse a COA using Cannlytics COA Data Extraction API.

        Args:
            coa_url: URL or path to COA PDF/document

        Returns:
            COAData object with extracted information, or None if parsing fails
        """
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Cannlytics COA extraction endpoint
                response = await client.post(
                    f"{self.base_url}/coa/extract",
                    json={"url": coa_url},
                    headers=self.headers
                )

                if response.status_code != 200:
                    return None

                data = response.json()

                # Parse results array for terpene data
                terpenes = {}
                totals = Totals()
                strain_name = None
                lab_name = None
                test_date = None
                batch_id = None

                # Extract from response structure
                # Note: Actual structure depends on Cannlytics API response format
                if "results" in data:
                    results = data["results"]

                    # Extract terpenes
                    for result in results:
                        analyte = result.get("name", "").lower()
                        value = result.get("value")

                        if value is not None:
                            # Map common terpene names
                            if "myrcene" in analyte:
                                terpenes["myrcene"] = float(value)
                            elif "limonene" in analyte:
                                terpenes["limonene"] = float(value)
                            elif "caryophyllene" in analyte:
                                terpenes["caryophyllene"] = float(value)
                            elif "pinene" in analyte:
                                if "alpha" in analyte or "α" in analyte:
                                    terpenes["alpha_pinene"] = float(value)
                                elif "beta" in analyte or "β" in analyte:
                                    terpenes["beta_pinene"] = float(value)
                            elif "terpinolene" in analyte:
                                terpenes["terpinolene"] = float(value)
                            elif "humulene" in analyte:
                                terpenes["humulene"] = float(value)
                            elif "linalool" in analyte:
                                terpenes["linalool"] = float(value)
                            elif "ocimene" in analyte:
                                terpenes["ocimene"] = float(value)

                            # Cannabinoids
                            elif analyte == "thc" or analyte == "delta-9-thc":
                                totals.thc = float(value)
                            elif analyte == "thca":
                                totals.thca = float(value)
                            elif analyte == "cbd":
                                totals.cbd = float(value)
                            elif analyte == "cbda":
                                totals.cbda = float(value)
                            elif "total" in analyte and "terpene" in analyte:
                                totals.total_terpenes = float(value)

                # Extract metadata
                strain_name = data.get("product_name") or data.get("strain_name")
                lab_name = data.get("lab", {}).get("name")
                test_date = data.get("date_tested")
                batch_id = data.get("batch_id")

                if not terpenes:
                    return None

                return COAData(
                    strain_name=strain_name,
                    terpenes=terpenes,
                    totals=totals,
                    lab_name=lab_name,
                    test_date=test_date,
                    batch_id=batch_id
                )

        except Exception as e:
            print(f"COA parsing error: {e}")
            return None

    async def get_strain_data(self, strain_name: str) -> Optional[StrainAPIData]:
        """
        Get strain terpene data from Cannlytics Strain Data API.

        Args:
            strain_name: Name of the strain to look up

        Returns:
            StrainAPIData with average terpene profile, or None if not found
        """
        try:
            import urllib.parse

            # URL encode the strain name
            encoded_name = urllib.parse.quote_plus(strain_name)

            async with httpx.AsyncClient(timeout=15.0) as client:
                # Cannlytics strain data endpoint (no auth required for public data)
                url = f"https://cannlytics.com/api/data/strains/{encoded_name}"
                print(f"Fetching strain data from: {url}")

                response = await client.get(url)

                if response.status_code != 200:
                    print(f"Strain API returned status {response.status_code}")
                    return None

                result = response.json()
                print(f"Strain API response: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")

                # Response format: {"data": {...}}
                if not result or "data" not in result:
                    print("No 'data' key in response")
                    return None

                strain = result["data"]

                # DEBUG: Print full strain data to see what's available
                import json
                print(f"DEBUG: Full strain data from Cannlytics:")
                print(json.dumps(strain, indent=2, default=str)[:2000])  # Limit to 2000 chars

                # Extract terpene averages
                terpenes = {}

                # Cannlytics API returns terpenes as direct fields on the strain object
                # Map their field names to our standard names
                terpene_mapping = {
                    'beta_myrcene': 'myrcene',
                    'myrcene': 'myrcene',
                    'd_limonene': 'limonene',
                    'limonene': 'limonene',
                    'beta_caryophyllene': 'caryophyllene',
                    'caryophyllene': 'caryophyllene',
                    'alpha_pinene': 'alpha_pinene',
                    'beta_pinene': 'beta_pinene',
                    'terpinolene': 'terpinolene',
                    'humulene': 'humulene',
                    'linalool': 'linalool',
                    'ocimene': 'ocimene',
                }

                for api_key, std_key in terpene_mapping.items():
                    if api_key in strain and strain[api_key] is not None:
                        try:
                            value = float(strain[api_key])
                            # Cannlytics returns percentages as decimals already (e.g., 0.26 = 0.26%)
                            # We need them as fractions (e.g., 0.0026 = 0.26%)
                            if value > 0:
                                terpenes[std_key] = value / 100
                        except (ValueError, TypeError):
                            pass

                # Extract cannabinoid data
                totals = Totals()
                cannabinoid_mapping = {
                    'thc': 'thc',
                    'delta_9_thc': 'thc',  # Use delta-9 if regular THC not present
                    'thca': 'thca',
                    'thcv': 'thcv',
                    'cbd': 'cbd',
                    'cbda': 'cbda',
                    'cbdv': 'cbdv',
                    'cbn': 'cbn',
                    'cbg': 'cbg',
                    'cbgm': 'cbgm',
                    'cbgv': 'cbgv',
                    'cbc': 'cbc',
                    'cbcv': 'cbcv',
                    'cbv': 'cbv',
                    'cbe': 'cbe',
                    'cbt': 'cbt',
                    'cbl': 'cbl',
                    'total_terpenes': 'total_terpenes',
                }

                for api_key, std_key in cannabinoid_mapping.items():
                    if api_key in strain and strain[api_key] is not None:
                        try:
                            value = float(strain[api_key])
                            # Cannlytics returns percentages as decimals (e.g., 18.13 = 18.13%)
                            # We need them as fractions (e.g., 0.1813 = 18.13%)
                            if value > 0:
                                setattr(totals, std_key, value / 100 if value > 1 else value)
                        except (ValueError, TypeError):
                            pass

                # Return data even if no terpenes found (cannabinoids might be present)
                if not terpenes and not any([totals.thc, totals.cbd, totals.cbn, totals.cbg]):
                    print("No terpene or cannabinoid data found in strain response")
                    return None

                print(f"Extracted {len(terpenes)} terpenes and cannabinoid data from API")

                return StrainAPIData(
                    strain_name=strain.get("strain_name") or strain.get("name", strain_name),
                    terpenes=terpenes,
                    totals=totals,
                    match_score=1.0,  # Exact match assumed
                    source="cannlytics"
                )

        except Exception as e:
            print(f"Strain API error: {e}")
            return None
