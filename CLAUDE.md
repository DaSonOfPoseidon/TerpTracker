# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TerpTracker is a web application that analyzes cannabis strain terpene profiles and classifies them into SDP (Strain Data Project) categories. It uses multi-source data merging to combine page scraping, COA parsing, database lookups (50k+ strains), and API calls to provide the most complete terpene profiles possible.

## Tech Stack

**Backend (FastAPI):**
- FastAPI with async support
- PostgreSQL for data storage (50k+ strain profiles: 32k dataset + 21k cached)
- Redis for caching and rate limiting
- Playwright for JS-rendered page scraping
- Cannlytics API integration for COA parsing and strain data (active)
- Public Dataset: Terpene Profile Parser (32,874 strains, auto-imported on first launch)
- Multi-source data merging with priority-based conflict resolution
- RapidFuzz for fuzzy strain name matching
- **API Status**: Cannlytics (active) | Kushy (offline) | Otreeba (offline)

**Frontend (Next.js):**
- Next.js 14 with App Router
- React 18 with TypeScript
- Tailwind CSS + shadcn/ui components
- PWA support for mobile-first experience

## Development Commands

### Setup

```bash
# Start all services with Docker Compose
docker-compose up -d

# Backend setup (if running locally without Docker)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Frontend setup (if running locally without Docker)
cd frontend
npm install
```

### Running Locally

```bash
# Backend (from /backend directory)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (from /frontend directory)
npm run dev

# With Docker (from project root)
docker-compose up
```

### Testing

```bash
# Backend tests
cd backend
pytest                           # Run all tests
pytest tests/test_classifier.py  # Run specific test file
pytest -v                        # Verbose output
pytest --cov=app                 # With coverage

# Frontend tests
cd frontend
npm test                         # Run Vitest tests
```

### Building for Production

```bash
# Frontend build
cd frontend
npm run build
npm start  # Run production build

# Backend (use Docker for production)
docker build -t terptracker-backend ./backend
docker build -t terptracker-frontend ./frontend
```

## Architecture

### Analysis Pipeline (Multi-Source Merging)

The core analysis flow uses intelligent multi-source data collection and merging:

1. **Scraper** (app/services/scraper.py): Playwright renders JS-heavy pages and extracts terpene data, COA links, strain names, and cannabinoids using regex patterns
2. **COA Parser** (app/services/cannlytics_client.py): If COA links found, ALWAYS attempts to parse with Cannlytics API for lab-quality data
3. **Database Lookup** (app/services/profile_cache.py): ALWAYS checks PostgreSQL for cached strain profiles (50k+ strains)
4. **Conditional API Call** (app/services/analyzer.py): If merged data has <5 terpenes OR is missing major cannabinoids (THC/CBD/CBG/CBN), queries Cannlytics Strain Data API
5. **Data Merging** (app/services/analyzer.py): Intelligently merges all collected data with priority: **COA > Page > Database > API**
   - `merge_terpene_data()` - Combines terpenes from all sources
   - `merge_cannabinoid_data()` - Combines cannabinoids from all sources
   - For each compound, uses highest priority source that has it
   - Conflicts resolved automatically by priority
6. **Classifier** (app/services/classifier.py): Pure function classifies merged terpene profile into 6 SDP categories (BLUE/YELLOW/PURPLE/GREEN/ORANGE/RED)
7. **Summary Generator**: Creates friendly one-liner based on category and terpene composition
8. **Database Caching**: Saves merged results back to PostgreSQL for future lookups

**Response Format Change**: `source: str` → `sources: List[str]` to track all contributing sources (e.g., `["page", "database"]`)

### SDP Categories

Classification rules (from app/services/classifier.py):
- **ORANGE**: Terpinolene ≥35% or dominant
- **GREEN**: α+β-Pinene ≥35% or dominant
- **BLUE**: Myrcene ≥35% or dominant
- **PURPLE**: Caryophyllene ≥30% AND Pinene ≤15%
- **YELLOW**: Limonene ≥30%
- **RED**: Myrcene, Limonene, Caryophyllene balanced (≥20% each, within ±15%, low Pinene/Humulene)

### Key Files

**Backend:**
- `app/services/classifier.py` - Core SDP classification logic (pure function, easy to test)
- `app/services/scraper.py` - Playwright-based page scraping with regex extraction
- `app/services/analyzer.py` - Main orchestration service with multi-source merging logic
  - `merge_terpene_data()` - Merges terpenes from COA/page/database/API with priority
  - `merge_cannabinoid_data()` - Merges cannabinoids with priority
  - `is_data_complete()` - Checks if API supplementation needed
- `app/services/cannlytics_client.py` - Cannlytics API integration (COA parsing + strain data)
- `app/services/kushy_client.py` - Kushy API integration (currently offline)
- `app/services/otreeba_client.py` - Otreeba API integration (currently offline)
- `app/services/profile_cache.py` - PostgreSQL strain profile caching service
- `app/data/init_datasets.py` - Automatic dataset download and import on first launch
- `app/api/routes.py` - FastAPI endpoints: POST /api/analyze-url, GET /api/terpenes/{key}
- `app/db/models.py` - SQLAlchemy models for extractions, profiles, terpene_defs, cache

**Frontend:**
- `app/page.tsx` - Main page with URL input form and result display
- `components/AnalyzeForm.tsx` - URL input form with loading states
- `components/ResultCard.tsx` - Results display with SDP color coding
- `components/TerpenePanel.tsx` - Expandable accordion with terpene information
- `lib/api.ts` - API client functions for backend communication
- `lib/utils.ts` - Category colors, formatting utilities

### Database

PostgreSQL tables:
- `extractions` - Scraping results and metadata
- `profiles` - Normalized strain terpene profiles with SDP categories
- `terpene_defs` - Static terpene information (effects, aroma, etc.)
- `cache` - General key-value cache (Redis handles short-term caching)

### Caching Strategy

- **Redis**: 15-minute cache for analysis results, rate limiting state
- **PostgreSQL**: Long-term storage of strain profiles and extraction history
  - ~32,874 profiles from Terpene Profile Parser dataset
  - ~3,088 profiles from Phytochemical Diversity dataset (14 terpenes + 6 cannabinoids)
  - Thousands of profiles from Cannlytics Cannabis Results (7 US states, lab-tested)
  - Additional profiles from previous user searches (page scraping, COAs, APIs)
  - Deduplication by normalized strain name
  - Profiles include terpenes, cannabinoids, SDP category, and provenance metadata
  - OpenTHC Variety Database provides strain name normalization (3,000+ names)

### Dataset Initialization

On first Docker container launch, `app/data/init_datasets.py` automatically imports 4 datasets, each with an independent marker file:

1. **[1/4] Terpene Profile Parser** (GitHub) — ~32,874 strains, 9 terpenes + cannabinoids
2. **[2/4] Phytochemical Diversity** (GitHub) — ~3,088 unique strains averaged from ~90k lab samples, 14 terpenes + 6 cannabinoids (CC0 license)
3. **[3/4] OpenTHC Variety Database** — 3,000+ strain name mappings for alias-aware lookups (no terpene data, name normalization only)
4. **[4/4] Cannlytics Cannabis Results** (HuggingFace) — state-by-state lab results from 7 US states (CC BY 4.0). States imported: NY, UT, CT, CO, FL, NV, CA. Parser supports both individual terpene columns and JSON `results` column formats. Removed: HI, RI, MA, OR, MD, MI (no usable terpene data). WA excluded (XLSX only)

Each dataset is independently try/except wrapped — one failure doesn't block others. Markers are per-dataset in `backend/app/data/downloads/`:
- `.initialized_terpene_parser`
- `.initialized_phytochem`
- `.initialized_openthc`
- `.initialized_cannlytics`
- `.initialized` (legacy, counts as terpene_parser done)

**To force re-initialization of a specific dataset:** Delete the corresponding `.initialized_*` marker and restart the container.
**To force full re-initialization:** Delete all `.initialized*` markers in `backend/app/data/downloads/`

## Notes

- Use # for comments instead of """ (per user preference)
- Always update documentation and testing after adding new features
- Do not make commits automatically
- Classifier is a pure function - keep it that way for testability
- Respect robots.txt when scraping; only scrape user-provided URLs

## Data Sources & API Status

**Active Datasets (auto-imported on first launch):**
- ✅ Terpene Profile Parser (~32k strains) - Public GitHub dataset
- ✅ Phytochemical Diversity (~3k strains, 14 terpenes) - GitHub, CC0 license
- ✅ Cannlytics Cannabis Results (thousands of strains, 7 US states) - HuggingFace, CC BY 4.0
- ✅ OpenTHC Variety Database (3k+ strain names) - Name normalization only

**Active APIs:**
- ✅ Cannlytics API (COA parsing + strain data) - Requires API key

**Offline/Unavailable:**
- ❌ Kushy API - Free strain database, went offline in 2025
- ❌ Otreeba API - Commercial API, service appears unavailable (can't create accounts)

**Integration Pattern for New Datasets:**
1. Add parser function in `app/data/init_datasets.py` following existing patterns
2. Add marker key to `MARKERS` dict and download URL
3. Add import step in `initialize_datasets()` flow
4. For runtime APIs: create client in `app/services/{api_name}_client.py`
5. Add to API fallback chain in `analyzer.py`
6. Update documentation and tests
