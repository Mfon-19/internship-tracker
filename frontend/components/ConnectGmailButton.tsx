"use client";

import { supabaseBrowser } from "@/lib/supabaseClient";

export function ConnectGmailButton({ isConnected }: { isConnected: boolean }) {
  const handleConnect = async () => {
    await supabaseBrowser.auth.signInWithOAuth({
      provider: "google",
      options: {
        scopes: "https://www.googleapis.com/auth/gmail.readonly",
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
        redirectTo: `${window.location.origin}/auth/gmail-callback`,
      },
    });
  };

  return (
    <button
      type="button"
      onClick={handleConnect}
      className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
    >
      {isConnected ? "Reconnect Gmail" : "Connect Gmail"}
    </button>
  );
}
