"use client";

import { supabaseBrowser } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";

export function SignOutButton() {
  const router = useRouter();

  const handleSignOut = async () => {
    await supabaseBrowser.auth.signOut();
    router.push("/login");
  };

  return (
    <button
      type="button"
      onClick={handleSignOut}
      className="inline-flex items-center justify-center rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-800 shadow-sm hover:bg-slate-100"
    >
      Sign out
    </button>
  );
}
