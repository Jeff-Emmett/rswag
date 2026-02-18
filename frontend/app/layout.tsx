import type { Metadata } from "next";
import { GeistSans } from "geist/font";
import { cookies } from "next/headers";
import "./globals.css";
import type { SpaceConfig } from "@/lib/spaces";
import { themeToCSS } from "@/lib/spaces";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function getSpaceConfig(spaceId: string): Promise<SpaceConfig | null> {
  try {
    const res = await fetch(`${API_URL}/spaces/${spaceId}`, {
      next: { revalidate: 300 },
    });
    if (res.ok) return res.json();
  } catch {}
  return null;
}

export async function generateMetadata(): Promise<Metadata> {
  const cookieStore = await cookies();
  const spaceId = cookieStore.get("space_id")?.value || "default";
  const space = await getSpaceConfig(spaceId);

  const name = space?.name || "rSwag";
  const tagline = space?.tagline || "Merch for the rSpace Ecosystem";
  return {
    title: `${name} — ${tagline}`,
    description: space?.description || "Design and order custom merchandise.",
  };
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const spaceId = cookieStore.get("space_id")?.value || "default";
  const space = await getSpaceConfig(spaceId);

  const name = space?.name || "rSwag";
  const footerText = space?.footer_text || "rSpace. Infrastructure for the commons.";
  const logoUrl = space?.logo_url;
  const themeCSS = space?.theme ? themeToCSS(space.theme) : "";

  return (
    <html lang="en">
      <head>
        {themeCSS && (
          <style
            dangerouslySetInnerHTML={{
              __html: `:root {\n    ${themeCSS}\n  }`,
            }}
          />
        )}
      </head>
      <body className={GeistSans.className}>
        <div className="min-h-screen flex flex-col">
          <header className="border-b">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
              <a href="/" className="flex items-center gap-2 text-xl font-bold text-primary">
                {logoUrl && (
                  <img src={logoUrl} alt="" className="h-8 w-8 rounded" />
                )}
                {name}
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
              <p>&copy; 2026 {footerText}</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
