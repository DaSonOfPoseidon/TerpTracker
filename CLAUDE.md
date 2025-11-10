# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TerpTracker is a web application that analyzes cannabis strain terpene profiles and classifies them into SDP (Strain Data Project) categories. It scrapes product pages, parses COAs, and provides friendly summaries of terpene compositions.

## Tech Stack

**Backend (FastAPI):**
- FastAPI with async support
- PostgreSQL for data storage
- Redis for caching and rate limiting
- Playwright for JS-rendered page scraping
- Cannlytics API integration for COA parsing and strain data
- RapidFuzz for fuzzy strain name matching

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

### Analysis Pipeline

The core analysis flow follows this sequence:

1. **Scraper** (app/services/scraper.py): Playwright renders JS-heavy pages and extracts terpene data, COA links, and strain names using regex patterns
2. **COA Parser** (app/services/cannlytics_client.py): If COA links found, parse with Cannlytics API for lab-quality data
3. **Strain Fallback** (app/services/analyzer.py): If no data found, fuzzy-match strain name and query Cannlytics Strain Data API
4. **Classifier** (app/services/classifier.py): Pure function classifies terpene profile into 6 SDP categories (BLUE/YELLOW/PURPLE/GREEN/ORANGE/RED)
5. **Summary Generator**: Creates friendly one-liner based on category and terpene composition

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
- `app/services/analyzer.py` - Main orchestration service tying together scraping, COA, API fallback
- `app/services/cannlytics_client.py` - Cannlytics API integration
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

- Redis: 15-minute cache for analysis results, rate limiting state
- PostgreSQL: Long-term storage of profiles and extraction history

## Notes

- Use # for comments instead of """ (per user preference)
- Always update documentation and testing after adding new features
- Do not make commits automatically
- Classifier is a pure function - keep it that way for testability
- Respect robots.txt when scraping; only scrape user-provided URLs
