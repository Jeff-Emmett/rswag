"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getSpaceIdFromCookie, getCartKey } from "@/lib/spaces";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface ProductVariant {
  name: string;
  sku: string;
  provider: string;
  price: number;
}

interface Product {
  slug: string;
  name: string;
  description: string;
  category: string;
  product_type: string;
  tags: string[];
  image_url: string;
  base_price: number;
  variants: ProductVariant[];
  is_active: boolean;
}

const MOCKUP_TYPES = [
  { type: "shirt", label: "T-Shirt" },
  { type: "sticker", label: "Sticker" },
  { type: "print", label: "Art Print" },
];

function getMockupType(productType: string): string {
  if (productType.includes("shirt") || productType.includes("tee") || productType.includes("hoodie")) return "shirt";
  if (productType.includes("sticker")) return "sticker";
  if (productType.includes("print")) return "print";
  return "shirt";
}

export default function ProductPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [selectedMockup, setSelectedMockup] = useState<string>("shirt");
  const [quantity, setQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);
  const [addedToCart, setAddedToCart] = useState(false);

  useEffect(() => {
    async function fetchProduct() {
      try {
        const res = await fetch(`${API_URL}/products/${slug}`);
        if (!res.ok) {
          setError(res.status === 404 ? "Product not found" : "Failed to load product");
          return;
        }
        const data = await res.json();
        setProduct(data);
        if (data.variants?.length > 0) {
          setSelectedVariant(data.variants[0]);
        }
        setSelectedMockup(getMockupType(data.product_type));
      } catch {
        setError("Failed to load product");
      } finally {
        setLoading(false);
      }
    }
    if (slug) fetchProduct();
  }, [slug]);

  const getOrCreateCart = async (): Promise<string | null> => {
    let cartId = localStorage.getItem(getCartKey(getSpaceIdFromCookie()));
    if (cartId) {
      try {
        const res = await fetch(`${API_URL}/cart/${cartId}`);
        if (res.ok) return cartId;
      } catch { /* cart expired */ }
    }
    try {
      const res = await fetch(`${API_URL}/cart`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        cartId = data.id;
        localStorage.setItem(getCartKey(getSpaceIdFromCookie()), cartId!);
        return cartId;
      }
    } catch { return null; }
    return null;
  };

  const handleAddToCart = async () => {
    if (!product || !selectedVariant) return;
    setAddingToCart(true);
    try {
      const cartId = await getOrCreateCart();
      if (!cartId) { alert("Failed to create cart"); return; }

      const res = await fetch(`${API_URL}/cart/${cartId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_slug: product.slug,
          variant_sku: selectedVariant.sku,
          quantity,
        }),
      });

      if (res.ok) {
        setAddedToCart(true);
        setTimeout(() => setAddedToCart(false), 3000);
      } else {
        const data = await res.json();
        alert(data.detail || "Failed to add to cart");
      }
    } catch { alert("Failed to add to cart"); }
    finally { setAddingToCart(false); }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">{error || "Product not found"}</h1>
        <Link href="/products" className="text-primary hover:underline">Back to Products</Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-8 text-sm">
        <Link href="/" className="text-muted-foreground hover:text-primary">Home</Link>
        <span className="mx-2 text-muted-foreground">/</span>
        <Link href="/products" className="text-muted-foreground hover:text-primary">Products</Link>
        <span className="mx-2 text-muted-foreground">/</span>
        <span className="text-foreground">{product.name}</span>
      </nav>

      <div className="grid md:grid-cols-2 gap-12">
        {/* Product Mockup Image */}
        <div>
          <div className="aspect-square bg-muted rounded-lg overflow-hidden mb-4">
            <img
              src={`${API_URL}/designs/${product.slug}/mockup?type=${selectedMockup}`}
              alt={`${product.name} on ${selectedMockup}`}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Mockup type switcher — preview on different products */}
          <div className="flex gap-2">
            {MOCKUP_TYPES.map((mt) => (
              <button
                key={mt.type}
                onClick={() => setSelectedMockup(mt.type)}
                className={`flex-1 py-2 px-3 rounded-md border text-sm font-medium transition-colors ${
                  selectedMockup === mt.type
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-muted-foreground/30 hover:border-primary text-muted-foreground"
                }`}
              >
                {mt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Product Details */}
        <div>
          <div className="mb-2">
            <span className="text-sm text-muted-foreground capitalize">
              {product.category} / {product.product_type}
            </span>
          </div>

          <h1 className="text-3xl font-bold mb-4">{product.name}</h1>
          <p className="text-muted-foreground mb-6">{product.description}</p>

          <div className="text-3xl font-bold mb-6">
            ${selectedVariant?.price.toFixed(2) || product.base_price.toFixed(2)}
          </div>

          {/* Variant Selection */}
          {product.variants && product.variants.length > 1 && (
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Select Option</label>
              <div className="flex flex-wrap gap-2">
                {product.variants.map((variant) => (
                  <button
                    key={variant.sku}
                    onClick={() => setSelectedVariant(variant)}
                    className={`px-4 py-2 rounded-md border transition-colors ${
                      selectedVariant?.sku === variant.sku
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-muted-foreground/30 hover:border-primary"
                    }`}
                  >
                    {variant.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Quantity */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Quantity</label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-10 h-10 rounded-md border flex items-center justify-center hover:bg-muted transition-colors"
              >
                -
              </button>
              <span className="w-12 text-center font-medium">{quantity}</span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="w-10 h-10 rounded-md border flex items-center justify-center hover:bg-muted transition-colors"
              >
                +
              </button>
            </div>
          </div>

          {/* Add to Cart */}
          <button
            onClick={handleAddToCart}
            disabled={addingToCart || !selectedVariant}
            className={`w-full py-4 rounded-md font-medium transition-colors ${
              addedToCart
                ? "bg-green-600 text-white"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {addingToCart ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Adding...
              </span>
            ) : addedToCart ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Added to Cart!
              </span>
            ) : (
              "Add to Cart"
            )}
          </button>

          {addedToCart && (
            <Link href="/cart" className="block text-center mt-4 text-primary hover:underline">
              View Cart
            </Link>
          )}

          {/* Tags */}
          {product.tags?.length > 0 && (
            <div className="mt-8 pt-6 border-t">
              <span className="text-sm text-muted-foreground">Tags: </span>
              <div className="flex flex-wrap gap-2 mt-2">
                {product.tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 text-xs bg-muted rounded-full">{tag}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
