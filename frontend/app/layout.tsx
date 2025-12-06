import type { Metadata } from "next";
import "./globals.css";
import { createSupabaseServerClient } from "@/lib/supabaseServer";
import { SignOutButton } from "@/components/SignOutButton";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Internship Tracker",
  description: "Track internship and job applications ingested from Gmail",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = createSupabaseServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b bg-white">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <Link href="/" className="text-2xl font-semibold">
                Internship / Job Tracker
              </Link>
              <p className="text-sm text-slate-500">Supabase + Gmail ingestion</p>
            </div>
            <div className="flex items-center gap-3">
              {session?.user?.email && (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-800">
                  {session.user.email}
                </span>
              )}
              {session ? (
                <SignOutButton />
              ) : (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800">Guest</span>
              )}
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
