"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

export function SupportForm() {
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  return (
    <form
      className="mt-8 space-y-4"
      onSubmit={async (event) => {
        event.preventDefault();
        setSending(true);
        setStatus(null);
        const response = await fetch("/api/support", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, subject, message }),
        });
        const data = await response.json();
        setSending(false);
        if (!response.ok) {
          setStatus(data.error || "Could not submit your request.");
          return;
        }
        setStatus("Your request was submitted. ForeFixed support will review it.");
        setSubject("");
        setMessage("");
      }}
    >
      <label className="block text-sm">
        <span className="font-medium text-[var(--color-foreground)]">Email</span>
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-3"
        />
      </label>
      <label className="block text-sm">
        <span className="font-medium text-[var(--color-foreground)]">Subject</span>
        <input
          required
          minLength={3}
          maxLength={160}
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
          className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-3"
        />
      </label>
      <label className="block text-sm">
        <span className="font-medium text-[var(--color-foreground)]">How can we help?</span>
        <textarea
          required
          minLength={10}
          maxLength={4000}
          rows={6}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          className="mt-1 w-full resize-y rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-3"
        />
      </label>
      {status && <p role="status" className="text-sm text-[var(--color-muted)]">{status}</p>}
      <Button type="submit" disabled={sending}>
        {sending ? "Submitting..." : "Submit request"}
      </Button>
    </form>
  );
}
