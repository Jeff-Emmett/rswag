"""Design service for reading designs from the designs directory."""

from pathlib import Path
from functools import lru_cache

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.schemas.design import Design, DesignSource, DesignProduct
from app.schemas.product import Product, ProductVariant
from app.models.product import ProductOverride

settings = get_settings()


class DesignService:
    """Service for reading and managing designs."""

    def __init__(self):
        self.designs_path = settings.designs_dir
        self._cache: dict[str, Design] = {}

    def clear_cache(self):
        """Clear the design cache."""
        self._cache.clear()

    async def list_designs(
        self,
        status: str = "active",
        category: str | None = None,
    ) -> list[Design]:
        """List all designs from the designs directory."""
        designs = []

        if not self.designs_path.exists():
            return designs

        for category_dir in self.designs_path.iterdir():
            if not category_dir.is_dir():
                continue

            # Filter by category if specified
            if category and category_dir.name != category:
                continue

            for design_dir in category_dir.iterdir():
                if not design_dir.is_dir():
                    continue

                design = await self._load_design(design_dir, category_dir.name)
                if design and design.status == status:
                    designs.append(design)

        return designs

    async def get_design(self, slug: str) -> Design | None:
        """Get a single design by slug."""
        # Check cache
        if slug in self._cache:
            return self._cache[slug]

        # Search for the design
        for category_dir in self.designs_path.iterdir():
            if not category_dir.is_dir():
                continue

            design_dir = category_dir / slug
            if design_dir.exists():
                design = await self._load_design(design_dir, category_dir.name)
                if design:
                    self._cache[slug] = design
                    return design

        return None

    async def get_design_image_path(self, slug: str) -> str | None:
        """Get the path to the design image file."""
        design = await self.get_design(slug)
        if not design:
            return None

        # Look for exported PNG first
        for category_dir in self.designs_path.iterdir():
            if not category_dir.is_dir():
                continue

            design_dir = category_dir / slug
            if not design_dir.exists():
                continue

            # Check exports/300dpi first
            export_path = design_dir / "exports" / "300dpi" / f"{slug}.png"
            if export_path.exists():
                return str(export_path)

            # Check for source PNG
            source_path = design_dir / design.source.file
            if source_path.exists() and source_path.suffix.lower() == ".png":
                return str(source_path)

            # Check for any PNG in the directory
            for png_file in design_dir.glob("*.png"):
                return str(png_file)

        return None

    async def _load_design(self, design_dir: Path, category: str) -> Design | None:
        """Load a design from its directory."""
        metadata_path = design_dir / "metadata.yaml"
        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path) as f:
                metadata = yaml.safe_load(f)
        except Exception:
            return None

        if not metadata:
            return None

        slug = metadata.get("slug", design_dir.name)

        # Parse source info
        source_data = metadata.get("source", {})
        source = DesignSource(
            file=source_data.get("file", f"{slug}.svg"),
            format=source_data.get("format", "svg"),
            dimensions=source_data.get("dimensions", {"width": 0, "height": 0}),
            dpi=source_data.get("dpi", 300),
            color_profile=source_data.get("color_profile", "sRGB"),
        )

        # Parse products
        products = []
        for p in metadata.get("products", []):
            products.append(
                DesignProduct(
                    type=p.get("type", ""),
                    provider=p.get("provider", ""),
                    sku=str(p.get("sku", "")),  # Convert to string (some SKUs are integers)
                    variants=p.get("variants", []),
                    retail_price=float(p.get("retail_price", 0)),
                )
            )

        return Design(
            slug=slug,
            name=metadata.get("name", slug),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            category=category,
            author=metadata.get("author", ""),
            created=str(metadata.get("created", "")),
            source=source,
            products=products,
            status=metadata.get("status", "draft"),
            image_url=f"/api/designs/{slug}/image",
        )

    async def list_products(
        self,
        category: str | None = None,
        product_type: str | None = None,
    ) -> list[Product]:
        """List all products (designs formatted for storefront)."""
        designs = await self.list_designs(status="active", category=category)
        products = []

        for design in designs:
            # Skip designs with no products
            if not design.products:
                continue

            # Filter by product type if specified
            matching_products = [
                dp for dp in design.products
                if not product_type or dp.type == product_type
            ]

            if not matching_products:
                continue

            # Use the first matching product for base info, combine all variants
            dp = matching_products[0]
            all_variants = []

            for mp in matching_products:
                if mp.variants:
                    for v in mp.variants:
                        all_variants.append(
                            ProductVariant(
                                name=f"{v} ({mp.provider})",
                                sku=f"{mp.sku}-{v}",
                                provider=mp.provider,
                                price=mp.retail_price,
                            )
                        )
                else:
                    all_variants.append(
                        ProductVariant(
                            name=f"default ({mp.provider})",
                            sku=mp.sku,
                            provider=mp.provider,
                            price=mp.retail_price,
                        )
                    )

            products.append(
                Product(
                    slug=design.slug,
                    name=design.name,
                    description=design.description,
                    category=design.category,
                    product_type=dp.type,
                    tags=design.tags,
                    image_url=design.image_url,
                    base_price=dp.retail_price,
                    variants=all_variants,
                    is_active=True,
                )
            )

        return products

    async def get_product(self, slug: str) -> Product | None:
        """Get a single product by slug."""
        design = await self.get_design(slug)
        if not design or not design.products:
            return None

        # Use the first product configuration
        dp = design.products[0]
        variants = [
            ProductVariant(
                name=v,
                sku=f"{dp.sku}-{v}",
                provider=dp.provider,
                price=dp.retail_price,
            )
            for v in dp.variants
        ] if dp.variants else [
            ProductVariant(
                name="default",
                sku=dp.sku,
                provider=dp.provider,
                price=dp.retail_price,
            )
        ]

        return Product(
            slug=design.slug,
            name=design.name,
            description=design.description,
            category=design.category,
            product_type=dp.type,
            tags=design.tags,
            image_url=design.image_url,
            base_price=dp.retail_price,
            variants=variants,
            is_active=True,
        )

    async def set_product_override(
        self,
        db: AsyncSession,
        slug: str,
        is_active: bool | None = None,
        price_override: float | None = None,
    ):
        """Set a product override in the database."""
        # Check if override exists
        result = await db.execute(
            select(ProductOverride).where(ProductOverride.slug == slug)
        )
        override = result.scalar_one_or_none()

        if override:
            if is_active is not None:
                override.is_active = is_active
            if price_override is not None:
                override.price_override = price_override
        else:
            override = ProductOverride(
                slug=slug,
                is_active=is_active if is_active is not None else True,
                price_override=price_override,
            )
            db.add(override)

        await db.commit()
