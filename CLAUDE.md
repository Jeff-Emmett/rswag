# rSwag - AI Assistant Context

## Project Overview

E-commerce platform for rSpace ecosystem merchandise (stickers, shirts, prints) with Mollie payments and print-on-demand fulfillment via Printful and Prodigi. Part of the rSpace ecosystem (rspace.online).

## Architecture

- **Frontend**: Next.js 15 App Router, shadcn/ui, Tailwind CSS, Geist font
- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL
- **Payments**: Mollie (redirect flow, Dutch data residency)
- **Fulfillment**: Printful (apparel), Prodigi (stickers/prints)
- **AI Design**: Gemini API for design generation
- **Deployment**: Docker on Netcup RS 8000, Traefik routing

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `backend/app/api/` | FastAPI route handlers |
| `backend/app/models/` | SQLAlchemy ORM models |
| `backend/app/schemas/` | Pydantic request/response schemas |
| `backend/app/services/` | Business logic (mollie, pod, orders, spaces) |
| `backend/app/pod/` | POD provider clients |
| `frontend/app/` | Next.js App Router pages |
| `frontend/components/` | React components |
| `frontend/lib/` | Utilities (spaces, cn) |
| `designs/` | Design assets (stickers, shirts, misc) |
| `spaces/` | Space configs (multi-tenant branding/theming) |

## Spaces (Multi-Tenant)

rSwag supports subdomain-based spaces. Each space has its own branding, theme, and product catalog.

- **Config**: `spaces/{space_id}/space.yaml` defines name, theme colors, design filter, tips
- **Subdomain routing**: `{space}.rswag.online` detected by Next.js middleware, sets `space_id` cookie
- **API filtering**: `GET /api/products?space=fungiflows` returns only that space's designs
- **Theme injection**: CSS variables overridden at runtime from space config
- **Cart isolation**: localStorage keys scoped by space (`cart_id_fungiflows`)
- **Current spaces**: `_default` (rSwag hub), `fungiflows` (Fungi Flows merch)

## Design Source

Designs are stored in-repo at `./designs/` and mounted into the backend container.

Each design has a `metadata.yaml` with name, description, products, variants, pricing, and `space` field.

## API Endpoints

### Spaces
- `GET /api/spaces` - List all spaces
- `GET /api/spaces/{id}` - Get space config (branding, theme, tips)

### Public
- `GET /api/designs` - List active designs (optional: `?space=X`)
- `GET /api/designs/{slug}` - Get design details
- `GET /api/designs/{slug}/image` - Serve design image
- `GET /api/products` - List products with variants (optional: `?space=X`)
- `POST /api/cart` - Create cart
- `GET/POST/DELETE /api/cart/{id}/items` - Cart operations
- `POST /api/checkout/session` - Create Mollie payment
- `GET /api/orders/{id}` - Order status (requires email)
- `POST /api/design/generate` - AI design generation

### Webhooks
- `POST /api/webhooks/mollie` - Mollie payment events
- `POST /api/webhooks/prodigi` - Prodigi fulfillment updates
- `POST /api/webhooks/printful` - Printful fulfillment updates

### Admin (JWT required)
- `POST /api/admin/auth/login` - Admin login
- `GET /api/admin/orders` - List orders
- `GET /api/admin/analytics/*` - Sales metrics

## Deployment

Push to Gitea triggers webhook auto-deploy on Netcup at `/opt/apps/rswag/`.

## Branding

Default (rSwag):
- **Primary color**: Cyan (HSL 195 80% 45%)
- **Secondary color**: Orange (HSL 45 80% 55%)
- **Font**: Geist Sans + Geist Mono
- **Theme**: rSpace spatial web aesthetic

Fungi Flows space (`fungiflows.rswag.online`):
- **Primary**: Gold (#ffd700)
- **Secondary**: Bioluminescent green (#39ff14)
- **Background**: Deep purple (#08070d)
- **Theme**: Psychedelic mushroom hip-hop aesthetic
