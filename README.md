# TerpTracker

A web application that analyzes cannabis strain terpene profiles and classifies them into **Strain Data Project (SDP)** categories. Simply paste a product URL, and TerpTracker will extract terpene data, parse Certificates of Analysis (COAs, if provided), and provide a friendly summary with SDP color-coded categories.

## Features

- **Intelligent Extraction**: Uses Playwright to render JavaScript-heavy product pages and extract terpene data
- **COA Parsing**: Automatically detects and parses Certificate of Analysis documents using the Cannlytics API
- **Strain Database Fallback**: Falls back to Cannlytics Strain Data API with fuzzy name matching when on-page data isn't available
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
- **PostgreSQL** - Data storage for profiles and extractions
- **Redis** - Caching and rate limiting
- **Playwright** - Headless browser for JS-rendered pages
- **Cannlytics API** - COA parsing and strain data
- **RapidFuzz** - Fuzzy string matching for strain names

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
  "source": "coa",
  "terpenes": {
    "myrcene": 0.8,
    "limonene": 0.5,
    "caryophyllene": 0.4
  },
  "totals": {
    "total_terpenes": 2.1,
    "thca": 23.4
  },
  "category": "BLUE",
  "summary": "Strain's composition puts it in the BLUE category — expect myrcene-forward with an earthy, relaxing profile.",
  "strain_guess": "Blue Dream",
  "evidence": {
    "detection_method": "coa_parse",
    "coa_url": "https://example.com/coa.pdf",
    "coa_lab": "Genesis Testing Labs"
  }
}
```

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
- `CANNLYTICS_API_KEY` - Your Cannlytics API key
- `OTREEBA_API_KEY` - (Optional) Otreeba API key
- `RATE_LIMIT_PER_MINUTE` - Rate limit (default: 30)

**Frontend (.env):**
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Architecture

### Analysis Pipeline

1. **Page Scraping**: Playwright renders the page and extracts terpene data, COA links, and strain names
2. **COA Detection**: If COA links are found, parse them using Cannlytics API for lab-quality data
3. **API Fallback**: If no data found, fuzzy-match the strain name and query Cannlytics Strain Data API
4. **Classification**: Pure function classifies terpene profile into one of 6 SDP categories
5. **Summary Generation**: Creates a friendly one-liner based on category and composition

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

## Roadmap

- [ ] QR code detection and parsing for COAs
- [ ] Bulk strain analysis
- [ ] User accounts and saved analyses
- [ ] Additional data sources integration
- [ ] Mobile app (React Native)
- [ ] Advanced filtering and search
