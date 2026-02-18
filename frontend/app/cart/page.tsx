"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getSpaceIdFromCookie, getCartKey } from "@/lib/spaces";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface CartItem {
  id: string;
  product_slug: string;
  product_name: string;
  variant_sku: string;
  variant_name: string | null;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

interface Cart {
  id: string;
  items: CartItem[];
  item_count: number;
  subtotal: number;
}

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchCart = async () => {
    const cartKey = getCartKey(getSpaceIdFromCookie());
    const cartId = localStorage.getItem(cartKey);
    if (cartId) {
      try {
        const res = await fetch(`${API_URL}/cart/${cartId}`);
        if (res.ok) {
          const data = await res.json();
          setCart(data);
        } else {
          // Cart expired or deleted
          localStorage.removeItem(cartKey);
          setCart(null);
        }
      } catch {
        setCart(null);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const updateQuantity = async (itemId: string, newQuantity: number) => {
    if (!cart || newQuantity < 1) return;

    setUpdating(itemId);
    try {
      const res = await fetch(`${API_URL}/cart/${cart.id}/items/${itemId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantity: newQuantity }),
      });

      if (res.ok) {
        const updatedCart = await res.json();
        setCart(updatedCart);
      }
    } catch {
      console.error("Failed to update quantity");
    } finally {
      setUpdating(null);
    }
  };

  const removeItem = async (itemId: string) => {
    if (!cart) return;

    setUpdating(itemId);
    try {
      const res = await fetch(`${API_URL}/cart/${cart.id}/items/${itemId}`, {
        method: "DELETE",
      });

      if (res.ok) {
        const updatedCart = await res.json();
        setCart(updatedCart);
      }
    } catch {
      console.error("Failed to remove item");
    } finally {
      setUpdating(null);
    }
  };

  const handleCheckout = async () => {
    if (!cart) return;
    setCheckingOut(true);

    try {
      const res = await fetch(`${API_URL}/checkout/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cart_id: cart.id,
          success_url: `${window.location.origin}/checkout/success`,
          cancel_url: `${window.location.origin}/cart`,
        }),
      });

      if (res.ok) {
        const { checkout_url } = await res.json();
        window.location.href = checkout_url;
      } else {
        const data = await res.json();
        alert(data.detail || "Failed to start checkout");
      }
    } catch (error) {
      console.error("Checkout error:", error);
      alert("Failed to start checkout");
    } finally {
      setCheckingOut(false);
    }
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

  if (!cart || cart.items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">Your Cart</h1>
        <p className="text-muted-foreground mb-8">Your cart is empty.</p>
        <Link
          href="/products"
          className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          Continue Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-8">Your Cart</h1>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item) => (
            <div
              key={item.id}
              className={`flex items-center gap-4 p-4 border rounded-lg ${
                updating === item.id ? "opacity-50" : ""
              }`}
            >
              {/* Product Image */}
              <Link href={`/products/${item.product_slug}`}>
                <div className="w-24 h-24 bg-muted rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={`${API_URL}/designs/${item.product_slug}/image`}
                    alt={item.product_name}
                    className="w-full h-full object-cover"
                  />
                </div>
              </Link>

              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <Link
                  href={`/products/${item.product_slug}`}
                  className="font-semibold hover:text-primary transition-colors"
                >
                  {item.product_name}
                </Link>
                {item.variant_name && (
                  <p className="text-sm text-muted-foreground">
                    {item.variant_name}
                  </p>
                )}
                <p className="text-sm text-muted-foreground">
                  ${item.unit_price.toFixed(2)} each
                </p>

                {/* Quantity Controls */}
                <div className="flex items-center gap-2 mt-2">
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    disabled={updating === item.id || item.quantity <= 1}
                    className="w-8 h-8 rounded border flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-50"
                  >
                    -
                  </button>
                  <span className="w-8 text-center">{item.quantity}</span>
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    disabled={updating === item.id}
                    className="w-8 h-8 rounded border flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-50"
                  >
                    +
                  </button>
                  <button
                    onClick={() => removeItem(item.id)}
                    disabled={updating === item.id}
                    className="ml-4 text-sm text-red-600 hover:text-red-700 transition-colors disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              </div>

              {/* Subtotal */}
              <div className="text-right">
                <p className="font-bold">${item.subtotal.toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="border rounded-lg p-6 sticky top-4">
            <h2 className="font-bold text-lg mb-4">Order Summary</h2>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">
                  Subtotal ({cart.item_count} item{cart.item_count !== 1 ? "s" : ""})
                </span>
                <span>${cart.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>Shipping</span>
                <span>Calculated at checkout</span>
              </div>
            </div>
            <div className="border-t pt-4 mb-6">
              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span>${cart.subtotal.toFixed(2)}</span>
              </div>
            </div>
            <button
              onClick={handleCheckout}
              disabled={checkingOut}
              className="w-full bg-primary text-primary-foreground py-3 rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {checkingOut ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="animate-spin h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Processing...
                </span>
              ) : (
                "Proceed to Checkout"
              )}
            </button>
            <Link
              href="/products"
              className="block text-center mt-4 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
