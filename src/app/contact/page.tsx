import { LegalPage } from "@/components/LegalPage";
import { SupportForm } from "@/components/SupportForm";

export default function ContactPage() {
  return (
    <LegalPage title="Contact ForeFixed">
      <p>Send ForeFixed a message about MySwingCoaches. Support requests are stored securely and used only to respond and operate the service.</p>
      <SupportForm />
    </LegalPage>
  );
}
