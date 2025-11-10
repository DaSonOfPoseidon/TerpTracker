from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List
from datetime import datetime

# Terpene models
class TerpeneProfile(BaseModel):
    myrcene: Optional[float] = None
    limonene: Optional[float] = None
    caryophyllene: Optional[float] = None
    alpha_pinene: Optional[float] = None
    beta_pinene: Optional[float] = None
    terpinolene: Optional[float] = None
    humulene: Optional[float] = None
    linalool: Optional[float] = None
    ocimene: Optional[float] = None
    # Additional terpenes can be captured in extra fields

    class Config:
        extra = "allow"  # Allow additional terpene fields

class Totals(BaseModel):
    total_terpenes: Optional[float] = None
    thc: Optional[float] = None
    thca: Optional[float] = None
    cbd: Optional[float] = None
    cbda: Optional[float] = None

# Evidence/Provenance models
class Evidence(BaseModel):
    detection_method: str  # 'page_scrape' | 'coa_parse' | 'api_fallback'
    url: Optional[str] = None
    coa_url: Optional[str] = None
    coa_lab: Optional[str] = None
    coa_date: Optional[str] = None
    api_source: Optional[str] = None
    match_score: Optional[float] = None  # For fuzzy name matching
    raw_data: Optional[Dict] = None

# Request/Response models
class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl

class AnalyzeUrlResponse(BaseModel):
    source: str = Field(..., description="Data source: 'page' | 'coa' | 'api'")
    terpenes: Dict[str, float] = Field(..., description="Terpene profile with percentages")
    totals: Totals = Field(..., description="Total terpenes and cannabinoids")
    category: str = Field(..., description="SDP category: BLUE|YELLOW|PURPLE|GREEN|ORANGE|RED")
    summary: str = Field(..., description="Friendly one-liner about the profile")
    strain_guess: str = Field(..., description="Normalized strain name")
    evidence: Evidence = Field(..., description="Source and detection metadata")

class TerpeneInfo(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    effects: Optional[List[str]] = None
    aroma: Optional[str] = None
    also_found_in: Optional[List[str]] = None

# Internal models for services
class ScrapedData(BaseModel):
    strain_name: Optional[str] = None
    terpenes: Dict[str, float] = {}
    totals: Totals = Totals()
    coa_links: List[str] = []
    html_hash: str

class COAData(BaseModel):
    strain_name: Optional[str] = None
    terpenes: Dict[str, float]
    totals: Totals
    lab_name: Optional[str] = None
    test_date: Optional[str] = None
    batch_id: Optional[str] = None

class StrainAPIData(BaseModel):
    strain_name: str
    terpenes: Dict[str, float]
    match_score: float
    source: str  # 'cannlytics' | 'otreeba'
