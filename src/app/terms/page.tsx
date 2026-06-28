import { LegalPage } from "@/components/LegalPage";

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service">
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Service operator</h2>
        <p>ForeFixed. By creating an account or purchasing an analysis, you agree to these terms.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">AI-assisted coaching</h2>
        <p>Reports are generated with artificial intelligence from the video and profile information you provide. They are educational guidance, not medical advice, a guaranteed performance result, or instruction from a certified PGA professional.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Your responsibilities</h2>
        <p>You must upload only videos you own or have permission to use, provide accurate account information, practice safely, and stop any movement that causes pain. Do not upload unlawful, abusive, or unrelated content.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Payments and availability</h2>
        <p>Each purchase provides one analysis credit. Prices are shown before checkout. Service availability can be affected by third-party hosting, storage, payment, and AI providers.</p>
      </section>
      <section>
        <h2 className="text-lg font-semibold text-[var(--color-foreground)]">Limitation</h2>
        <p>To the maximum extent permitted by law, ForeFixed is not responsible for injury, lost play, scoring outcomes, or indirect damages resulting from use of the service.</p>
      </section>
      <p><strong className="text-[var(--color-foreground)]">Attorney review notice:</strong> These launch terms are an operational template and require review by qualified counsel.</p>
    </LegalPage>
  );
}
