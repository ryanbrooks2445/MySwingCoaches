import type { Metadata } from "next";
import { LegalPage } from "@/components/LegalPage";
import { SupportForm } from "@/components/SupportForm";

export const metadata: Metadata = {
  title: "Contact",
  description: "Contact ForeFixed about partnerships, press, or general questions.",
};

const supportEmail = process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim();

export default function ContactPage() {
  return (
    <LegalPage
      title="Contact ForeFixed"
      description="Partnerships, press, or general questions. For account and billing help, use Support."
    >
      {supportEmail ? (
        <p className="mb-6 text-sm text-[var(--color-muted)]">
          Email{" "}
          <a href={`mailto:${supportEmail}`} className="font-medium text-[var(--color-accent)] hover:underline">
            {supportEmail}
          </a>{" "}
          or send a message below.
        </p>
      ) : (
        <p className="mb-6 text-sm text-[var(--color-muted)]">
          Send a message below. We use contact requests only to respond and operate the service.
        </p>
      )}
      <SupportForm />
    </LegalPage>
  );
}
