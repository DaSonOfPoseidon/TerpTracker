from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import AnalyzeUrlRequest, AnalyzeUrlResponse, TerpeneInfo
from app.services.analyzer import StrainAnalyzer
from app.services.cache import cache_service
import hashlib

router = APIRouter()

# Static terpene information database
TERPENE_INFO = {
    "myrcene": TerpeneInfo(
        key="myrcene",
        name="β-Myrcene",
        description="The most common terpene in cannabis, known for its earthy, musky aroma with hints of cloves.",
        effects=["Relaxing", "Sedating", "Muscle relaxant"],
        aroma="Earthy, musky, herbal",
        also_found_in=["Hops", "Lemongrass", "Thyme", "Mango"]
    ),
    "limonene": TerpeneInfo(
        key="limonene",
        name="D-Limonene",
        description="Second most common terpene with a distinctive citrus aroma. Associated with mood elevation.",
        effects=["Uplifting", "Stress relief", "Mood enhancement"],
        aroma="Citrus, lemon, orange",
        also_found_in=["Citrus peels", "Juniper", "Peppermint"]
    ),
    "caryophyllene": TerpeneInfo(
        key="caryophyllene",
        name="β-Caryophyllene",
        description="Unique terpene that also acts as a cannabinoid, binding to CB2 receptors. Spicy and peppery.",
        effects=["Anti-inflammatory", "Pain relief", "Stress reduction"],
        aroma="Spicy, peppery, woody",
        also_found_in=["Black pepper", "Cloves", "Cinnamon", "Basil"]
    ),
    "pinene": TerpeneInfo(
        key="pinene",
        name="α-Pinene / β-Pinene",
        description="Sharp, pine-like terpene associated with alertness and memory retention.",
        effects=["Alertness", "Memory retention", "Bronchodilator"],
        aroma="Pine, sharp, fresh",
        also_found_in=["Pine needles", "Rosemary", "Basil", "Dill"]
    ),
    "terpinolene": TerpeneInfo(
        key="terpinolene",
        name="Terpinolene",
        description="Complex, multi-dimensional terpene with floral, herbal, and citrus notes.",
        effects=["Sedating", "Antioxidant", "Antibacterial"],
        aroma="Floral, herbal, piney, citrus",
        also_found_in=["Nutmeg", "Tea tree", "Cumin", "Lilacs"]
    ),
    "humulene": TerpeneInfo(
        key="humulene",
        name="α-Humulene",
        description="Earthy, woody terpene found in hops. Appetite suppressant properties.",
        effects=["Anti-inflammatory", "Appetite suppressant", "Pain relief"],
        aroma="Earthy, woody, spicy",
        also_found_in=["Hops", "Coriander", "Cloves", "Basil"]
    ),
    "linalool": TerpeneInfo(
        key="linalool",
        name="Linalool",
        description="Floral, lavender-like terpene known for calming and sedative effects.",
        effects=["Calming", "Sedative", "Anti-anxiety"],
        aroma="Floral, lavender, sweet",
        also_found_in=["Lavender", "Mint", "Cinnamon", "Coriander"]
    ),
    "ocimene": TerpeneInfo(
        key="ocimene",
        name="β-Ocimene",
        description="Sweet, herbaceous, and woody terpene with potential anti-inflammatory properties.",
        effects=["Uplifting", "Anti-inflammatory", "Antifungal"],
        aroma="Sweet, herbal, woody, citrus",
        also_found_in=["Mint", "Orchids", "Basil", "Pepper"]
    )
}

@router.post("/analyze-url", response_model=AnalyzeUrlResponse)
async def analyze_url(request: AnalyzeUrlRequest):
    """
    Analyze a URL to extract terpene profile and classify into SDP category.
    """
    url_str = str(request.url)

    # Check cache first
    cache_key = f"analysis:{hashlib.md5(url_str.encode()).hexdigest()}"
    cached = await cache_service.get(cache_key)

    if cached:
        return AnalyzeUrlResponse(**cached)

    try:
        # Analyze URL
        analyzer = StrainAnalyzer()
        result = await analyzer.analyze_url(url_str)

        # Cache result for 15 minutes
        await cache_service.set(cache_key, result.model_dump(), ttl=900)

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/terpenes/{key}", response_model=TerpeneInfo)
async def get_terpene_info(key: str):
    """
    Get detailed information about a specific terpene.
    """
    terpene = TERPENE_INFO.get(key.lower())

    if not terpene:
        raise HTTPException(status_code=404, detail=f"Terpene '{key}' not found")

    return terpene

@router.get("/terpenes", response_model=list[TerpeneInfo])
async def list_terpenes():
    """
    List all available terpene information.
    """
    return list(TERPENE_INFO.values())

@router.get("/version")
async def get_version():
    return {"version": "0.1.0", "api": "TerpTracker"}
