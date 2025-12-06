import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Internship Tracker",
  description: "Track internship and job applications ingested from Gmail",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <div className="space-y-1">
              <h1 className="text-2xl font-semibold">Internship / Job Tracker</h1>
              <p className="text-sm text-slate-500">Supabase + Gmail ingestion</p>
            </div>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
              Private workspace
            </span>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
