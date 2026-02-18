import type { Metadata } from "next";
import { GeistSans, GeistMono } from "geist/font";
import "./globals.css";

export const metadata: Metadata = {
  title: "rSwag — Merch for the rSpace Ecosystem",
  description: "Design and order custom merchandise for rSpace communities. Stickers, shirts, and more.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={GeistSans.className}>
        <div className="min-h-screen flex flex-col">
          <header className="border-b">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
              <a href="/" className="text-xl font-bold text-primary">
                rSwag
              </a>
              <nav className="flex items-center gap-6">
                <a href="/products" className="hover:text-primary">
                  Products
                </a>
                <a href="/design" className="px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
                  Design Swag
                </a>
                <a href="/cart" className="hover:text-primary">
                  Cart
                </a>
              </nav>
            </div>
          </header>
          <main className="flex-1">{children}</main>
          <footer className="border-t py-6">
            <div className="container mx-auto px-4 text-center text-muted-foreground">
              <p>&copy; 2026 rSpace. Infrastructure for the commons.</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
