import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Pay per swing or go unlimited annually. Secure Stripe checkout with a failed-analysis credit guarantee.",
};

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
