import { ApplicationTable, type Application } from "@/components/ApplicationTable";
import { ConnectGmailButton } from "@/components/ConnectGmailButton";
import { createSupabaseServerClient } from "@/lib/supabaseServer";
import { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Applications",
};

const stages = ["all", "applied", "interview", "offer", "rejected", "other"] as const;

type SearchParams = { stage?: string | string[]; q?: string | string[] };

type GmailConnection = {
  email: string;
  provider_refresh_token: string | null;
  watch_expiration: string | null;
};

export default async function Page({ searchParams }: { searchParams: SearchParams }) {
  const supabase = createSupabaseServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  const userId = session!.user.id;
  const stageParam = Array.isArray(searchParams.stage) ? searchParams.stage[0] : searchParams.stage;
  const queryParam = Array.isArray(searchParams.q) ? searchParams.q[0] : searchParams.q;
  const stage = stageParam && stages.includes(stageParam as any) ? stageParam : "all";
  const queryText = queryParam?.trim();

  let query = supabase
    .from("applications")
    .select("id, company, role, stage, email_date, source, subject")
    .eq("user_id", userId)
    .order("email_date", { ascending: false, nullsFirst: false });

  if (stage && stage !== "all") {
    query = query.eq("stage", stage);
  }

  if (queryText) {
    query = query.or(
      `company.ilike.%${queryText}%,role.ilike.%${queryText}%,subject.ilike.%${queryText}%`
    );
  }

  const [{ data: applicationsData }, { data: connection }] = await Promise.all([
    query,
    supabase
      .from("gmail_connections")
      .select("email, provider_refresh_token, watch_expiration")
      .eq("user_id", userId)
      .maybe_single(),
  ]);

  const applications: Application[] = applicationsData || [];
  const gmailConnection = connection as GmailConnection | null;

  const counts = stages.reduce<Record<string, number>>((acc, key) => {
    acc[key] = key === "all" ? applications.length : applications.filter((a) => a.stage === key).length;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="grid gap-4 md:grid-cols-4">
          {stages.slice(1).map((s) => (
            <div key={s} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium capitalize text-slate-600">{s}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{counts[s]}</p>
            </div>
          ))}
        </div>
        <GmailStatus connection={gmailConnection} />
      </section>

      <Filters stage={stage} queryText={queryText} />

      <ApplicationTable data={applications} />
    </div>
  );
}

function Filters({ stage, queryText }: { stage: string; queryText?: string }) {
  return (
    <form className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center">
      <div className="flex items-center gap-2">
        <label className="text-sm font-semibold text-slate-700">Stage</label>
        <select
          name="stage"
          defaultValue={stage}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-inner focus:border-slate-400 focus:outline-none"
        >
          {stages.map((s) => (
            <option key={s} value={s}>
              {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-1 items-center gap-2">
        <label className="text-sm font-semibold text-slate-700">Search</label>
        <input
          type="text"
          name="q"
          placeholder="Company, role, subject"
          defaultValue={queryText}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-inner focus:border-slate-400 focus:outline-none"
        />
      </div>
      <button
        type="submit"
        className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
      >
        Apply
      </button>
    </form>
  );
}

function GmailStatus({ connection }: { connection: GmailConnection | null }) {
  const connected = Boolean(connection?.provider_refresh_token);
  const expiration = connection?.watch_expiration
    ? new Date(connection.watch_expiration).toLocaleString()
    : null;

  return (
    <div className="flex flex-col items-start gap-2 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-500" : "bg-amber-500"}`}
          aria-hidden
        />
        <p className="text-sm font-semibold text-slate-800">
          {connected ? "Gmail connected" : "Gmail not connected"}
        </p>
      </div>
      <p className="text-xs text-slate-600">
        {connected
          ? connection?.email || "Connected via Google"
          : "Connect your Gmail to ingest application emails."}
      </p>
      {expiration && <p className="text-xs text-slate-500">Watch expires: {expiration}</p>}
      <ConnectGmailButton isConnected={connected} />
    </div>
  );
}
