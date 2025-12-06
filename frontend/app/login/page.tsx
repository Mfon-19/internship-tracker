import { AuthButtons } from "@/components/AuthButtons";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Login",
};

export default function LoginPage() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center gap-6 text-center">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-slate-900">Sign in to continue</h1>
        <p className="text-sm text-slate-600">Use your Google account to access your applications.</p>
      </div>
      <AuthButtons />
    </div>
  );
}
