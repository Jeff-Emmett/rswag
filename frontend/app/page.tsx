import Link from "next/link";
import { cookies } from "next/headers";
import type { SpaceConfig } from "@/lib/spaces";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface Product {
  slug: string;
  name: string;
  description: string;
  category: string;
  product_type: string;
  image_url: string;
  base_price: number;
}

async function getProducts(spaceId: string): Promise<Product[]> {
  try {
    const params = new URLSearchParams();
    if (spaceId && spaceId !== "default") {
      params.set("space", spaceId);
    }
    const url = `${API_URL}/products${params.toString() ? `?${params}` : ""}`;
    const res = await fetch(url, { next: { revalidate: 60 } });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

async function getSpaceConfig(spaceId: string): Promise<SpaceConfig | null> {
  try {
    const res = await fetch(`${API_URL}/spaces/${spaceId}`, {
      next: { revalidate: 300 },
    });
    if (res.ok) return res.json();
  } catch {}
  return null;
}

export default async function HomePage() {
  const cookieStore = await cookies();
  const spaceId = cookieStore.get("space_id")?.value || "default";
  const [products, space] = await Promise.all([
    getProducts(spaceId),
    getSpaceConfig(spaceId),
  ]);

  const name = space?.name || "rSwag";
  const description =
    space?.description ||
    "Merch for the rSpace ecosystem. Stickers, shirts, and more — designed by the community, printed on demand.";

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-3xl mx-auto text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          {name}
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          {description}
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/products"
            className="inline-flex items-center justify-center rounded-md bg-primary px-8 py-3 text-lg font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Browse Products
          </Link>
          <Link
            href="/design"
            className="inline-flex items-center justify-center rounded-md border border-primary px-8 py-3 text-lg font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            Design Your Own
          </Link>
          <Link
            href="/upload"
            className="inline-flex items-center justify-center rounded-md border border-primary px-8 py-3 text-lg font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            Upload Your Own
          </Link>
        </div>
      </div>

      <div className="mt-24">
        <h2 className="text-2xl font-bold text-center mb-12">Featured Products</h2>
        {products.length === 0 ? (
          <p className="text-center text-muted-foreground">
            No products available yet. Check back soon!
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {products.map((product) => (
              <Link
                key={product.slug}
                href={`/products/${product.slug}`}
                className="group"
              >
                <div className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="aspect-square bg-muted relative overflow-hidden">
                    <img
                      src={`${API_URL}/designs/${product.slug}/image`}
                      alt={product.name}
                      className="object-cover w-full h-full group-hover:scale-105 transition-transform"
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold">{product.name}</h3>
                    <p className="text-sm text-muted-foreground capitalize">
                      {product.product_type}
                    </p>
                    <p className="font-bold mt-2">${product.base_price.toFixed(2)}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
