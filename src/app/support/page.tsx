import { LegalPage } from "@/components/LegalPage";
import { SupportForm } from "@/components/SupportForm";

export default function SupportPage() {
  return (
    <LegalPage title="Support">
      <p>Use this form for account, payment, upload, report, privacy, or refund questions. Never include passwords, API keys, or card numbers.</p>
      <SupportForm />
    </LegalPage>
  );
}
