# rSwag

Merchandise store for the **rSpace ecosystem** at **rswag.online**

## Stack

- **Frontend**: Next.js 15 + shadcn/ui + Tailwind CSS + Geist font
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL
- **Payments**: Stripe Checkout
- **Fulfillment**: Printful (apparel) + Prodigi (stickers/prints)
- **AI Design**: Gemini API for on-demand design generation

## Architecture

```
rswag.online
        │
        ▼
  Cloudflare Tunnel → Traefik
        │                │
        ▼                ▼
   Next.js (3000)   FastAPI (8000)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    PostgreSQL       Stripe          POD APIs
```

## Development

### Quick Start

```bash
cp .env.example .env
# Edit .env with your API keys

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Local Development (without Docker)

```bash
# Backend
cd backend
pip install -e .
uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
pnpm dev
```

## Project Structure

```
rswag/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/         # Route handlers
│   │   ├── models/      # SQLAlchemy ORM
│   │   ├── schemas/     # Pydantic models
│   │   ├── services/    # Business logic
│   │   └── pod/         # POD provider clients
│   └── alembic/         # Database migrations
├── frontend/             # Next.js 15 frontend
│   ├── app/             # App Router pages
│   ├── components/      # React components
│   └── lib/             # Utilities
├── designs/              # Design assets (in-repo)
│   ├── stickers/
│   ├── shirts/
│   └── misc/
└── config/               # POD provider config
```

## Deployment

Deployed on Netcup RS 8000 via Docker Compose with Traefik reverse proxy.

```bash
ssh netcup "cd /opt/apps/rswag && git pull && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
```
