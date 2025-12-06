import { supabaseAdmin } from "@/lib/supabaseAdmin";
import { createSupabaseServerClient } from "@/lib/supabaseServer";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const supabase = createSupabaseServerClient();

  if (code) {
    await supabase.auth.exchangeCodeForSession(code);
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session) {
    const providerToken = (session as any)?.provider_token as string | undefined;
    const providerRefreshToken = (session as any)?.provider_refresh_token as string | undefined;
    const expiresAt = providerToken ? new Date(Date.now() + 45 * 60 * 1000).toISOString() : null;

    await supabaseAdmin.from("gmail_connections").upsert(
      {
        user_id: session.user.id,
        email: session.user.email,
        provider_access_token: providerToken,
        provider_refresh_token: providerRefreshToken,
        provider_token_expires_at: expiresAt,
      },
      { onConflict: "user_id,email" }
    );

    const backendBase = process.env.BACKEND_BASE_URL;
    if (backendBase && session.user.email) {
      try {
        await fetch(`${backendBase}/gmail/watch`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ email: session.user.email }),
        });
      } catch (error) {
        console.error("Failed to trigger watch", error);
      }
    }
  }

  return NextResponse.redirect(new URL("/", request.url));
}
