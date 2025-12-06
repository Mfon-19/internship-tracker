import { format } from "date-fns";

export type Application = {
  id: string;
  company: string | null;
  role: string | null;
  stage: string;
  email_date: string | null;
  source: string | null;
  subject: string | null;
};

const stageColors: Record<string, string> = {
  applied: "bg-blue-100 text-blue-700",
  interview: "bg-amber-100 text-amber-700",
  rejected: "bg-rose-100 text-rose-700",
  offer: "bg-emerald-100 text-emerald-700",
  other: "bg-slate-100 text-slate-700",
};

export function ApplicationTable({ data }: { data: Application[] }) {
  return (
    <div className="table-card">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Company</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Role</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Stage</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Email Date</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Source</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Subject</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white text-sm">
          {data.map((app) => (
            <tr key={app.id} className="hover:bg-slate-50">
              <td className="px-4 py-3 font-medium">{app.company || "—"}</td>
              <td className="px-4 py-3">{app.role || "—"}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                    stageColors[app.stage] || stageColors.other
                  }`}
                >
                  {app.stage}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-600">
                {app.email_date ? format(new Date(app.email_date), "PP") : "—"}
              </td>
              <td className="px-4 py-3 text-slate-600">{app.source || "gmail"}</td>
              <td className="px-4 py-3 text-slate-600">{app.subject || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
