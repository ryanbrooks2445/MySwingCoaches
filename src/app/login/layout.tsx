import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Log in",
  description: "Log in to ForeFixed to upload swings and view your coaching reports.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
