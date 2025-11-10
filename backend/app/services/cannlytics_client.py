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
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Cannlytics strain data endpoint
                response = await client.get(
                    f"{self.base_url}/strains",
                    params={"name": strain_name},
                    headers=self.headers
                )

                if response.status_code != 200:
                    return None

                data = response.json()

                if not data or "strains" not in data or not data["strains"]:
                    return None

                # Take first result
                strain = data["strains"][0]

                # Extract terpene averages
                terpenes = {}
                terpene_data = strain.get("terpenes", {})

                for terp_key, terp_value in terpene_data.items():
                    # Normalize key names
                    std_key = terp_key.lower().replace("-", "_").replace(" ", "_")
                    if terp_value is not None:
                        terpenes[std_key] = float(terp_value)

                if not terpenes:
                    return None

                return StrainAPIData(
                    strain_name=strain.get("name", strain_name),
                    terpenes=terpenes,
                    match_score=1.0,  # Exact match assumed
                    source="cannlytics"
                )

        except Exception as e:
            print(f"Strain API error: {e}")
            return None
