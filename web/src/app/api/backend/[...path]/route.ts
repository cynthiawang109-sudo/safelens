import { NextRequest, NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export const maxDuration = 240;
type Context = { params: Promise<{ path: string[] }> };
async function forward(request: NextRequest, context: Context) {
  const { path } = await context.params;
  const endpoint = path.join("/");
  if (!(
    (request.method === "GET" &&
      (endpoint === "health" || /^report\/\d+$/.test(endpoint))) ||
    (request.method === "POST" && endpoint === "ask")
  ))
    return NextResponse.json(
      { detail: "Unknown API endpoint" },
      { status: 404 },
    );
  try {
    const base = (
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    ).replace(/\/$/, "");
    const upstream = await fetch(`${base}/${endpoint}`, {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      body: request.method === "POST" ? await request.text() : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(235_000),
    });
    return new NextResponse(await upstream.text(), {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("Content-Type") || "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Report service unavailable or request timed out" },
      { status: 502 },
    );
  }
}
export const GET = forward;
export const POST = forward;
