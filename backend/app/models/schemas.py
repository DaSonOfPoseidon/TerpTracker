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
    # Major cannabinoids
    thc: Optional[float] = None
    thca: Optional[float] = None
    thcv: Optional[float] = None
    cbd: Optional[float] = None
    cbda: Optional[float] = None
    cbdv: Optional[float] = None
    # Minor cannabinoids
    cbn: Optional[float] = None
    cbg: Optional[float] = None
    cbgm: Optional[float] = None
    cbgv: Optional[float] = None
    cbc: Optional[float] = None
    cbcv: Optional[float] = None
    cbv: Optional[float] = None
    cbe: Optional[float] = None
    cbt: Optional[float] = None
    cbl: Optional[float] = None

# Evidence/Provenance models
class Evidence(BaseModel):
    detection_method: str  # 'page_scrape' | 'coa_parse' | 'api_fallback'
    url: Optional[str] = None
    coa_url: Optional[str] = None
    coa_lab: Optional[str] = None
    coa_date: Optional[str] = None
    api_source: Optional[str] = None
    match_score: Optional[float] = None  # For fuzzy name matching
    cached_at: Optional[str] = None
    raw_data: Optional[Dict] = None

# Data availability tracking
class DataAvailability(BaseModel):
    has_terpenes: bool = False
    has_cannabinoids: bool = False
    has_coa: bool = False
    terpene_count: int = 0
    cannabinoid_count: int = 0

# Request/Response models
class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl

class AnalyzeUrlResponse(BaseModel):
    sources: List[str] = Field(..., description="Data sources used (in priority order): ['coa', 'page', 'database', 'api']")
    terpenes: Dict[str, float] = Field(default_factory=dict, description="Merged terpene profile with percentages from all sources")
    totals: Totals = Field(default_factory=Totals, description="Merged total terpenes and cannabinoids from all sources")
    category: Optional[str] = Field(None, description="SDP category: BLUE|YELLOW|PURPLE|GREEN|ORANGE|RED (null if no terpene data)")
    traditional_label: Optional[str] = Field(None, description="Traditional label from SDP research: Sativa|Modern Indica|Classic Indica|Hybrid")
    summary: str = Field(..., description="Friendly summary about the profile")
    strain_guess: str = Field(..., description="Normalized strain name")
    evidence: Evidence = Field(..., description="Source and detection metadata")
    data_available: DataAvailability = Field(default_factory=DataAvailability, description="What data was found")
    cannabinoid_insights: List[str] = Field(default_factory=list, description="Insights from cannabinoid ratios")

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
    totals: Totals = Totals()
    match_score: float
    source: str  # 'cannlytics' | 'otreeba'
