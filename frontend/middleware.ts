import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const host = request.headers.get("host") || "";
  const hostname = host.split(":")[0].toLowerCase();

  // Determine space from subdomain
  let spaceId = "default";
  if (hostname.endsWith(".rswag.online")) {
    spaceId = hostname.replace(".rswag.online", "");
  }
  // Local dev: check for space query param as override
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    const url = new URL(request.url);
    const spaceParam = url.searchParams.get("_space");
    if (spaceParam) {
      spaceId = spaceParam;
    }
  }

  const response = NextResponse.next();

  // Set cookie so both server and client components can read the space
  response.cookies.set("space_id", spaceId, {
    path: "/",
    sameSite: "lax",
    httpOnly: false,
    maxAge: 86400,
  });

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
