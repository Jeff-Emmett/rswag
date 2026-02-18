export interface SpaceTheme {
  primary: string;
  primary_foreground: string;
  secondary: string;
  secondary_foreground: string;
  background: string;
  foreground: string;
  card: string;
  card_foreground: string;
  popover: string;
  popover_foreground: string;
  muted: string;
  muted_foreground: string;
  accent: string;
  accent_foreground: string;
  destructive: string;
  destructive_foreground: string;
  border: string;
  input: string;
  ring: string;
}

export interface SpaceConfig {
  id: string;
  name: string;
  tagline: string;
  description: string;
  domain: string;
  footer_text: string;
  theme: SpaceTheme;
  design_filter: string;
  logo_url: string | null;
  design_tips: string[];
}

const THEME_VAR_MAP: Record<keyof SpaceTheme, string> = {
  primary: "--primary",
  primary_foreground: "--primary-foreground",
  secondary: "--secondary",
  secondary_foreground: "--secondary-foreground",
  background: "--background",
  foreground: "--foreground",
  card: "--card",
  card_foreground: "--card-foreground",
  popover: "--popover",
  popover_foreground: "--popover-foreground",
  muted: "--muted",
  muted_foreground: "--muted-foreground",
  accent: "--accent",
  accent_foreground: "--accent-foreground",
  destructive: "--destructive",
  destructive_foreground: "--destructive-foreground",
  border: "--border",
  input: "--input",
  ring: "--ring",
};

export function themeToCSS(theme: SpaceTheme): string {
  return Object.entries(THEME_VAR_MAP)
    .filter(([key]) => theme[key as keyof SpaceTheme])
    .map(([key, cssVar]) => `${cssVar}: ${theme[key as keyof SpaceTheme]};`)
    .join("\n    ");
}

/**
 * Get the localStorage key for the cart, scoped by space.
 */
export function getCartKey(spaceId?: string): string {
  if (!spaceId || spaceId === "default") return "cart_id";
  return `cart_id_${spaceId}`;
}

/**
 * Read space_id from document cookie (client-side only).
 */
export function getSpaceIdFromCookie(): string {
  if (typeof document === "undefined") return "default";
  const match = document.cookie.match(/(?:^|;\s*)space_id=([^;]*)/);
  return match ? match[1] : "default";
}
