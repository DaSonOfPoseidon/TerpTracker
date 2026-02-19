import hashlib
import logging
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import (
    AnalyzeUrlRequest, AnalyzeUrlResponse, TerpeneInfo,
    AnalyzeStrainRequest, StrainSearchResult, StrainSearchResponse,
    EffectsAnalysis, Evidence, DataAvailability, Totals,
)
from app.services.analyzer import StrainAnalyzer
from app.services.cache import cache_service
from app.services.profile_cache import profile_cache_service
from app.services.classifier import classify_terpene_profile, generate_summary, generate_cannabinoid_insights, get_traditional_label
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        logger.error("Analysis failed for URL %s", url_str, exc_info=True)
        detail = f"Analysis failed: {str(e)}" if settings.debug else "Analysis failed"
        raise HTTPException(status_code=500, detail=detail)

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

@router.get("/strains/autocomplete")
async def autocomplete_strains(q: str = Query(..., min_length=2), limit: int = Query(10, le=50)):
    """Fast prefix-only strain name autocomplete."""
    results = profile_cache_service.autocomplete_strains(q, limit=limit)
    return results

@router.get("/strains/search", response_model=StrainSearchResponse)
async def search_strains(q: str = Query(..., min_length=1), limit: int = Query(20, le=100)):
    """Search strains with prefix match + fuzzy matching."""
    results = profile_cache_service.search_strains(q, limit=limit)
    return StrainSearchResponse(
        results=[StrainSearchResult(**r) for r in results],
        total=len(results),
    )

@router.post("/analyze-strain", response_model=AnalyzeUrlResponse)
async def analyze_strain(request: AnalyzeStrainRequest):
    """Analyze a strain by name from the database."""
    strain_name = request.strain_name

    # Check Redis cache first
    cache_key = f"strain:{hashlib.md5(strain_name.lower().encode()).hexdigest()}"
    cached = await cache_service.get(cache_key)
    if cached:
        return AnalyzeUrlResponse(**cached)

    try:
        # Look up in DB
        cached_result = profile_cache_service.get_full_cached_result(strain_name)
        if not cached_result:
            raise HTTPException(status_code=404, detail=f"Strain '{strain_name}' not found in database")

        terpenes = cached_result['terpenes']
        totals = cached_result['totals']
        if isinstance(totals, dict):
            totals = Totals(**totals)

        # Classify if needed
        category = cached_result.get('category')
        if not category and terpenes:
            category = classify_terpene_profile(terpenes)

        # Generate summary
        if terpenes and category:
            summary = generate_summary(strain_name, category, terpenes)
        else:
            summary = f"{strain_name} - Data from database"

        # Generate cannabinoid insights
        cannabinoid_insights = generate_cannabinoid_insights(totals) if totals else []

        # Data availability
        has_terpenes = bool(terpenes)
        has_cannabinoids = any(getattr(totals, f, None) for f in ['thc', 'thca', 'cbd', 'cbda', 'cbn', 'cbg', 'cbc'])

        # Generate effects profile
        effects = None
        if has_terpenes and terpenes:
            from app.services.effects_engine import generate_effects_profile
            effects_data = generate_effects_profile(terpenes, totals, category)
            if effects_data:
                effects = EffectsAnalysis(**effects_data)

        result = AnalyzeUrlResponse(
            sources=["database"],
            terpenes=terpenes or {},
            totals=totals,
            category=category,
            traditional_label=get_traditional_label(category) if category else None,
            summary=summary,
            strain_guess=strain_name,
            evidence=Evidence(
                detection_method="database_cache",
                cached_at=cached_result.get('cached_at'),
            ),
            data_available=DataAvailability(
                has_terpenes=has_terpenes,
                has_cannabinoids=has_cannabinoids,
                has_coa=False,
                terpene_count=len(terpenes) if terpenes else 0,
                cannabinoid_count=sum(1 for f in ['thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv', 'cbn', 'cbg', 'cbc', 'cbcv']
                                      if getattr(totals, f, None)),
            ),
            cannabinoid_insights=cannabinoid_insights,
            effects=effects,
        )

        # Cache for 15 minutes
        await cache_service.set(cache_key, result.model_dump(), ttl=900)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Strain analysis failed for '%s'", strain_name, exc_info=True)
        detail = f"Analysis failed: {str(e)}" if settings.debug else "Analysis failed"
        raise HTTPException(status_code=500, detail=detail)

@router.get("/test-strain/{strain_name}")
async def test_strain_lookup(strain_name: str):
    """
    Test endpoint: Look up a strain directly by name using Cannlytics API.
    Bypasses scraping to verify API integration and classification pipeline.
    """
    from app.services.cannlytics_client import CannlyticsClient
    from app.services.classifier import classify_terpene_profile, generate_summary, generate_cannabinoid_insights

    try:
        client = CannlyticsClient()
        strain_data = await client.get_strain_data(strain_name)

        if not strain_data:
            raise HTTPException(status_code=404, detail=f"Strain '{strain_name}' not found in Cannlytics database")

        # Classify the terpene profile
        category = classify_terpene_profile(strain_data.terpenes) if strain_data.terpenes else None
        summary = generate_summary(strain_data.strain_name, category, strain_data.terpenes) if category else f"{strain_data.strain_name} - Data from Cannlytics API"

        # Generate cannabinoid insights
        cannabinoid_insights = generate_cannabinoid_insights(strain_data.totals)

        return {
            "strain_name": strain_data.strain_name,
            "terpenes": strain_data.terpenes,
            "totals": strain_data.totals.model_dump(),
            "category": category,
            "summary": summary,
            "cannabinoid_insights": cannabinoid_insights,
            "source": "cannlytics_api",
            "match_score": strain_data.match_score
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Test strain lookup failed for '%s'", strain_name, exc_info=True)
        detail = f"Lookup failed: {str(e)}" if settings.debug else "Lookup failed"
        raise HTTPException(status_code=500, detail=detail)
