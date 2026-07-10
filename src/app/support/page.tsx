import type { Metadata } from "next";
import { LegalPage } from "@/components/LegalPage";
import { SupportForm } from "@/components/SupportForm";

export const metadata: Metadata = {
  title: "Support",
  description: "Get help with ForeFixed accounts, payments, uploads, reports, privacy, or refunds.",
};

const supportEmail = process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim();

export default function SupportPage() {
  return (
    <LegalPage
      title="Support"
      description="Account, payment, upload, report, privacy, or refund questions. Never include passwords, API keys, or card numbers."
    >
      {supportEmail ? (
        <p className="mb-6 text-sm text-[var(--color-muted)]">
          Prefer email? Reach us at{" "}
          <a href={`mailto:${supportEmail}`} className="font-medium text-[var(--color-accent)] hover:underline">
            {supportEmail}
          </a>
          . Or use the form below — we store requests securely and use them only to respond.
        </p>
      ) : (
        <p className="mb-6 text-sm text-[var(--color-muted)]">
          Use the form below. Support requests are stored securely and used only to respond and operate the service.
        </p>
      )}
      <SupportForm />
    </LegalPage>
  );
}
