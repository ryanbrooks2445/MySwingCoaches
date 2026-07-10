import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign up",
  description: "Create a free ForeFixed account. Confirm your email, then upload a swing for analysis.",
};

export default function SignupLayout({ children }: { children: React.ReactNode }) {
  return children;
}
