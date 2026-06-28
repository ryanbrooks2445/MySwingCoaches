import { LegalPage } from "@/components/LegalPage";

export default function RefundPolicyPage() {
  return (
    <LegalPage title="Refund and Failed-Analysis Policy">
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Failed-analysis guarantee</h2>
        <p>If ForeFixed cannot complete an analysis after its automatic retries, the analysis credit is restored automatically. You can use it for another qualifying upload without paying again.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Completed analyses</h2>
        <p>Because a completed analysis is a delivered digital service, completed reports are generally non-refundable. ForeFixed may approve exceptions for duplicate charges, material delivery defects, or circumstances required by law.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Requesting help</h2>
        <p>Use the support form with the account email, approximate purchase date, and a brief description. Do not send card details.</p>
      </section>
      <p><strong className="text-[var(--color-foreground)]">Attorney review notice:</strong> Consumer cancellation rights vary by location and require legal review.</p>
    </LegalPage>
  );
}
