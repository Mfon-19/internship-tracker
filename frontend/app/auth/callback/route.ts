import { createSupabaseServerClient } from "@/lib/supabaseServer";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const supabase = createSupabaseServerClient();

  if (code) {
    try {
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      if (error) {
        console.error("Auth error:", error);
        return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(error.message)}`, request.url));
      }
    } catch (err) {
      console.error("Callback error:", err);
      return NextResponse.redirect(new URL("/login?error=server_error", request.url));
    }
  }

  return NextResponse.redirect(new URL("/", request.url));
}
