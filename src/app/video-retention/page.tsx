import { LegalPage } from "@/components/LegalPage";

export default function VideoRetentionPage() {
  return (
    <LegalPage title="Video Retention Policy">
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Default retention</h2>
        <p>Original swing videos are stored privately and scheduled for deletion 30 days after upload. Generated report text may remain in your account until you delete the swing or account.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Earlier deletion</h2>
        <p>You may delete a swing at any time from your dashboard. This removes the report, source video, and generated frames associated with that swing.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Retries after expiration</h2>
        <p>Once the source video has been removed, a failed or older report cannot be reprocessed. Upload a new swing to receive another analysis.</p>
      </section>
    </LegalPage>
  );
}
