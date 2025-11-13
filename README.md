# TerpTracker

A web application that analyzes cannabis strain terpene profiles and classifies them into **Strain Data Project (SDP)** categories. Simply paste a product URL, and TerpTracker will extract terpene data, parse Certificates of Analysis (COAs, if provided), and provide a friendly summary with SDP color-coded categories.

## Features

- **Multi-Source Data Merging**: Intelligently combines data from page scraping, COAs, local database (32k+ strains), and APIs to provide the most complete profile possible
- **Automatic Dataset Initialization**: On first launch, downloads and imports 32,874 lab-tested strain profiles from public datasets
- **Intelligent Extraction**: Uses Playwright to render JavaScript-heavy product pages and extract terpene data
- **COA Parsing**: Automatically detects and parses Certificate of Analysis documents using the Cannlytics API
- **PostgreSQL-Backed Database**: 21k+ cached strain profiles from previous searches, supplemented by 32k+ dataset strains
- **Smart API Supplementation**: Conditionally queries external APIs (Cannlytics) only when local data is incomplete
- **SDP Classification**: Categorizes strains into 6 color-coded categories (BLUE, YELLOW, PURPLE, GREEN, ORANGE, RED)
- **Mobile-First PWA**: Installable progressive web app optimized for mobile devices
- **Caching & Rate Limiting**: Redis-powered caching and rate limiting for optimal performance
- **Terpene Education**: Expandable panels with detailed information about each terpene

## SDP Categories

TerpTracker classifies strains based on their dominant terpene profiles:

- 🔵 **BLUE** - Myrcene-dominant: Earthy, relaxing profile
- 🟡 **YELLOW** - Limonene-dominant: Bright, citrus-leaning, upbeat profile
- 🟣 **PURPLE** - Caryophyllene-dominant: Spicy, peppery, balanced profile
- 🟢 **GREEN** - Pinene-dominant: Sharp, pine-like, alert profile
- 🟠 **ORANGE** - Terpinolene-dominant: Complex, floral, citrus notes
- 🔴 **RED** - Balanced: Equal myrcene-limonene-caryophyllene

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Data storage for 50k+ strain profiles, extractions, and cache
- **Redis** - Caching and rate limiting
- **Playwright** - Headless browser for JS-rendered pages
- **Cannlytics API** - COA parsing and strain data (active)
- **Public Datasets** - Terpene Profile Parser (32k+ lab-tested strains, auto-imported)
- **RapidFuzz** - Fuzzy string matching for strain names
- **Multi-Source Merging** - Intelligent data combination with priority-based conflict resolution

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Beautiful, accessible UI components
- **PWA Support** - Installable mobile app experience

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended)
- OR: Python 3.11+, Node.js 20+, PostgreSQL 15+, Redis 7+

### Quick Start with Docker

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TerpTracker.git
cd TerpTracker
```

2. Set up environment variables:
```bash
# Backend
cp backend/.env.example backend/.env
# Add your Cannlytics API key to backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env and add your API keys

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Start development server
npm run dev
```

## API Endpoints

### `POST /api/analyze-url`
Analyze a product URL and extract terpene profile.

**Request:**
```json
{
  "url": "https://example.com/products/strain-name"
}
```

**Response:**
```json
{
  "sources": ["coa", "page", "database"],
  "terpenes": {
    "myrcene": 0.8,
    "limonene": 0.5,
    "caryophyllene": 0.4,
    "alpha_pinene": 0.3,
    "humulene": 0.2
  },
  "totals": {
    "total_terpenes": 2.1,
    "thc": 0.72,
    "thca": 0.234
  },
  "category": "BLUE",
  "summary": "Blue Dream's composition puts it in the BLUE category — expect myrcene-forward with an earthy, relaxing profile.",
  "strain_guess": "Blue Dream",
  "evidence": {
    "detection_method": "coa_parse",
    "coa_url": "https://example.com/coa.pdf",
    "coa_lab": "Genesis Testing Labs"
  },
  "data_available": {
    "has_terpenes": true,
    "has_cannabinoids": true,
    "has_coa": true,
    "terpene_count": 5,
    "cannabinoid_count": 2
  }
}
```

**Note**: The `sources` array shows all data sources that contributed to the result. Data is merged with priority: COA > Page > Database > API.

### `GET /api/terpenes/{key}`
Get detailed information about a specific terpene.

### `GET /api/terpenes`
List all available terpene information.

## Testing

```bash
# Backend tests
cd backend
pytest
pytest --cov=app  # With coverage

# Frontend tests
cd frontend
npm test
```

## Deployment

### Docker Production Build

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

**Backend (.env):**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `CANNLYTICS_API_KEY` - Your Cannlytics API key (required for COA parsing and strain data API)
- `OTREEBA_API_KEY` - (Optional, currently offline) Otreeba API key
- `RATE_LIMIT_PER_MINUTE` - Rate limit (default: 30)

**Note on Dataset Initialization:**
On first container launch, TerpTracker automatically downloads and imports the Terpene Profile Parser dataset (32,874 lab-tested strain profiles, ~7.4MB) from GitHub. This creates a `.initialized` marker file in `backend/app/data/downloads/` to prevent re-downloading on subsequent launches.

**Frontend (.env):**
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Architecture

### Analysis Pipeline (Multi-Source Merging)

TerpTracker uses an intelligent multi-source data collection and merging strategy to provide the most complete terpene profiles:

1. **Page Scraping**: Playwright renders the page and extracts terpene data, COA links, strain names, and cannabinoids
2. **COA Parsing**: If COA links found, always attempts to parse them using Cannlytics API for lab-quality data
3. **Database Lookup**: Always checks PostgreSQL database for cached strain profiles (50k+ strains including 32k from public datasets)
4. **Conditional API Supplementation**: If merged data has <5 terpenes or is missing major cannabinoids, queries Cannlytics Strain Data API
5. **Intelligent Merging**: Combines all collected data with priority: **COA > Page > Database > API**
   - For each terpene/cannabinoid, uses the highest priority source
   - Conflicts automatically resolved by priority
6. **Classification**: Pure function classifies merged terpene profile into one of 6 SDP categories
7. **Summary Generation**: Creates friendly one-liner based on category and composition
8. **Database Caching**: Saves merged results back to database for future lookups

**Example Multi-Source Result:**
- Page scraping finds 3 terpenes + cannabinoids
- Database has complete 8-terpene profile for same strain
- System merges both → returns all 8 terpenes with `sources: ["page", "database"]`

### Directory Structure

```
TerpTracker/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, middleware
│   │   ├── db/           # Database models
│   │   ├── models/       # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── tests/            # Pytest tests
│   └── alembic/          # Database migrations
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # Utilities, API client
│   └── __tests__/        # Vitest tests
└── docker-compose.yml    # Docker orchestration
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `pytest` (backend) and `npm test` (frontend)
5. Commit your changes: `git commit -m "Add feature"`
6. Push to the branch: `git push origin feature-name`
7. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Strain Data Project** for SDP terpene category definitions
- **Cannlytics** for COA parsing and strain data APIs
- **shadcn/ui** for beautiful UI components

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation in `CLAUDE.md`

## Data Sources & APIs

TerpTracker combines multiple data sources to provide comprehensive strain information:

### Active Sources
- ✅ **Cannlytics API** - COA parsing and strain data (active, requires API key)
- ✅ **Terpene Profile Parser Dataset** - 32,874 lab-tested strains (public, auto-imported)
- ✅ **Local PostgreSQL Database** - 50k+ cached strain profiles from all sources

### Offline/Unavailable Sources
- ❌ **Kushy API** - Previously free strain database (currently offline as of 2025)
- ❌ **Otreeba API** - Commercial strain data API (service appears offline, can't create accounts)

### Looking for More Data Sources

We're actively interested in integrating additional cannabis strain databases and APIs but have found limited options. Many previously-available free APIs have gone offline, and commercial alternatives are scarce or cost-prohibitive.

**If you know of active cannabis strain data APIs or public datasets**, please open an issue or PR! We're particularly interested in:
- Terpene profile databases (lab-tested data preferred)
- Cannabinoid analysis datasets
- Strain genetics/lineage information
- Commercial dispensary APIs with batch-specific COA data

## Roadmap

- [x] Multi-source data merging
- [x] Automatic dataset initialization
- [ ] QR code detection and parsing for COAs
- [ ] Additional data sources integration (seeking active APIs)
- [ ] Bulk strain analysis
- [ ] User accounts and saved analyses
- [ ] Mobile app (React Native)
- [ ] Advanced filtering and search
- [ ] Strain recommendation engine
