# rSwag - AI Assistant Context

## Project Overview

E-commerce platform for rSpace ecosystem merchandise (stickers, shirts, prints) with Stripe payments and print-on-demand fulfillment via Printful and Prodigi. Part of the rSpace ecosystem (rspace.online).

## Architecture

- **Frontend**: Next.js 15 App Router, shadcn/ui, Tailwind CSS, Geist font
- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL
- **Payments**: Stripe Checkout (redirect flow)
- **Fulfillment**: Printful (apparel), Prodigi (stickers/prints)
- **AI Design**: Gemini API for design generation
- **Deployment**: Docker on Netcup RS 8000, Traefik routing

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `backend/app/api/` | FastAPI route handlers |
| `backend/app/models/` | SQLAlchemy ORM models |
| `backend/app/schemas/` | Pydantic request/response schemas |
| `backend/app/services/` | Business logic (stripe, pod, orders) |
| `backend/app/pod/` | POD provider clients |
| `frontend/app/` | Next.js App Router pages |
| `frontend/components/` | React components |
| `designs/` | Design assets (stickers, shirts, misc) |

## Design Source

Designs are stored in-repo at `./designs/` and mounted into the backend container.

Each design has a `metadata.yaml` with name, description, products, variants, and pricing.

## API Endpoints

### Public
- `GET /api/designs` - List active designs
- `GET /api/designs/{slug}` - Get design details
- `GET /api/designs/{slug}/image` - Serve design image
- `GET /api/products` - List products with variants
- `POST /api/cart` - Create cart
- `GET/POST/DELETE /api/cart/{id}/items` - Cart operations
- `POST /api/checkout/session` - Create Stripe checkout
- `GET /api/orders/{id}` - Order status (requires email)
- `POST /api/design/generate` - AI design generation

### Webhooks
- `POST /api/webhooks/stripe` - Stripe payment events
- `POST /api/webhooks/prodigi` - Prodigi fulfillment updates
- `POST /api/webhooks/printful` - Printful fulfillment updates

### Admin (JWT required)
- `POST /api/admin/auth/login` - Admin login
- `GET /api/admin/orders` - List orders
- `GET /api/admin/analytics/*` - Sales metrics

## Deployment

Push to Gitea triggers webhook auto-deploy on Netcup at `/opt/apps/rswag/`.

## Branding

- **Primary color**: Cyan (HSL 195 80% 45%)
- **Secondary color**: Orange (HSL 45 80% 55%)
- **Font**: Geist Sans + Geist Mono
- **Theme**: rSpace spatial web aesthetic
