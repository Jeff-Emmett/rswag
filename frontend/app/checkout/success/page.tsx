"use client";

import { useEffect } from "react";
import Link from "next/link";
import { getSpaceIdFromCookie, getCartKey } from "@/lib/spaces";

export default function CheckoutSuccessPage() {
  useEffect(() => {
    // Clear cart after successful payment
    const cartKey = getCartKey(getSpaceIdFromCookie());
    localStorage.removeItem(cartKey);
  }, []);

  return (
    <div className="container mx-auto px-4 py-16 text-center">
      <div className="max-w-md mx-auto">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-8 h-8 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold mb-4">Order Confirmed!</h1>
        <p className="text-muted-foreground mb-8">
          Thank you for your purchase. Your order is being processed and
          you&apos;ll receive a confirmation email shortly.
        </p>
        <Link
          href="/products"
          className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          Continue Shopping
        </Link>
      </div>
    </div>
  );
}
