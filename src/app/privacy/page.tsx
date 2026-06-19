import { LegalPage } from "@/components/LegalPage";

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy">
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Information we process</h2>
        <p>ForeFixed processes account details, golfer profile information, payment references, uploaded swing videos, generated frames, AI reports, support messages, and basic security logs.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">How it is used</h2>
        <p>We use this information to authenticate you, securely process payments, analyze your swing, personalize coaching, prevent abuse, provide support, and maintain the service.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Service providers</h2>
        <p>Supabase provides authentication, database, and private storage. Google Gemini processes uploaded swing content to generate analysis. Stripe processes payments. Vercel and Google Cloud host application services. These providers process data under their own terms and security controls.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Retention and deletion</h2>
        <p>Source swing videos are scheduled for deletion after 30 days. Written reports may remain until you delete the report or your account. Account deletion permanently removes application data; payment providers may retain records required for legal and fraud-prevention purposes.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Your choices</h2>
        <p>You may delete individual swings, delete your account, or contact support about access and privacy questions. Videos are stored in private buckets and accessed through short-lived signed links.</p>
      </section>
      <p><strong className="text-[var(--color-foreground)]">Attorney review notice:</strong> This launch policy requires review for the jurisdictions where ForeFixed sells the service.</p>
    </LegalPage>
  );
}
