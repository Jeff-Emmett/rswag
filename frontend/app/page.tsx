import Link from "next/link";

interface Product {
  slug: string;
  name: string;
  description: string;
  category: string;
  product_type: string;
  image_url: string;
  base_price: number;
}

async function getProducts(): Promise<Product[]> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/products`,
      { next: { revalidate: 60 } } // Revalidate every minute
    );
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const products = await getProducts();

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-3xl mx-auto text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          rSwag
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          Merch for the rSpace ecosystem. Stickers, shirts,
          and more — designed by the community, printed on demand.
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
                      src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/designs/${product.slug}/image`}
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
