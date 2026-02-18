import Link from "next/link";
import { cookies } from "next/headers";

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
    const res = await fetch(url, { next: { revalidate: 3600 } });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function ProductsPage() {
  const cookieStore = await cookies();
  const spaceId = cookieStore.get("space_id")?.value || "default";
  const products = await getProducts(spaceId);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Products</h1>

      {products.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-muted-foreground">
            No products available yet. Check back soon!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
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
                  <h3 className="font-semibold truncate">{product.name}</h3>
                  <p className="text-sm text-muted-foreground capitalize">
                    {product.product_type}
                  </p>
                  <p className="font-bold mt-2">
                    ${product.base_price.toFixed(2)}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
