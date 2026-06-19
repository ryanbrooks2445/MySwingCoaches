"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { isGolferProfileComplete, type GolferProfileFields } from "@/lib/player-profile";
import { cn } from "@/lib/utils";

interface GolferProfileFormProps {
  onCompleteChange?: (complete: boolean) => void;
  className?: string;
}

export function GolferProfileForm({ onCompleteChange, className }: GolferProfileFormProps) {
  const [age, setAge] = useState("");
  const [yearsPlaying, setYearsPlaying] = useState("");
  const [average9Score, setAverage9Score] = useState("");
  const [typicalMiss, setTypicalMiss] = useState("");
  const [primaryGoal, setPrimaryGoal] = useState("");
  const [limitations, setLimitations] = useState("");
  const [noLimitations, setNoLimitations] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/profile");
        const data = await readApiResponse<{
          profile?: GolferProfileFields;
          complete?: boolean;
        }>(res);
        if (!res.ok) throw new Error(data.error || "Failed to load profile");
        const p = data.profile;
        if (!p) throw new Error("Could not load profile");
        if (p.age != null) setAge(String(p.age));
        if (p.years_playing != null) setYearsPlaying(String(p.years_playing));
        if (p.average_9_score != null) setAverage9Score(String(p.average_9_score));
        if (p.typical_miss) setTypicalMiss(p.typical_miss);
        if (p.primary_goal) setPrimaryGoal(p.primary_goal);
        if (p.physical_limitations === "None reported") {
          setNoLimitations(true);
          setLimitations("");
        } else if (p.physical_limitations) {
          setLimitations(p.physical_limitations);
        }
        const isComplete = Boolean(data.complete);
        setComplete(isComplete);
        setSaved(isComplete);
        onCompleteChange?.(isComplete);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load profile");
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- notify parent once after load
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      const res = await fetch("/api/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          age,
          years_playing: yearsPlaying,
          physical_limitations: limitations,
          no_physical_limitations: noLimitations,
          average_9_score: average9Score,
          typical_miss: typicalMiss,
          primary_goal: primaryGoal,
        }),
      });
      const data = await readApiResponse<{ complete?: boolean }>(res);
      if (!res.ok) throw new Error(data.error || "Failed to save profile");

      const isComplete = Boolean(data.complete);
      setComplete(isComplete);
      setSaved(true);
      onCompleteChange?.(isComplete);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
      onCompleteChange?.(false);
    } finally {
      setSaving(false);
    }
  }

  const draftComplete = isGolferProfileComplete({
    age: age ? parseInt(age, 10) : null,
    years_playing: yearsPlaying ? parseInt(yearsPlaying, 10) : null,
    physical_limitations: noLimitations ? "None reported" : limitations,
    average_9_score: average9Score ? parseInt(average9Score, 10) : null,
    typical_miss: typicalMiss,
    primary_goal: primaryGoal,
  });

  if (loading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <div className="h-32 rounded-lg bg-[var(--color-border)]/40" />
      </Card>
    );
  }

  return (
    <Card className={cn("border-[var(--color-accent)]/25", className)}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-accent)]">
            Required before upload
          </p>
          <h2 className="mt-1 text-lg font-semibold">Your golfer profile</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            We tailor drills and feels to your age, experience, and body — pain-free coaching only.
          </p>
        </div>
        {complete && saved && (
          <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-500">
            Saved
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="mt-6 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="font-medium">Age</span>
            <input
              type="number"
              min={5}
              max={120}
              required
              value={age}
              onChange={(e) => {
                setAge(e.target.value);
                setSaved(false);
              }}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="e.g. 52"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Years playing golf</span>
            <input
              type="number"
              min={0}
              max={100}
              required
              value={yearsPlaying}
              onChange={(e) => {
                setYearsPlaying(e.target.value);
                setSaved(false);
              }}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="e.g. 25"
            />
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="font-medium">Average 9-hole score</span>
            <input
              type="number"
              min={25}
              max={90}
              required
              value={average9Score}
              onChange={(e) => {
                setAverage9Score(e.target.value);
                setSaved(false);
              }}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="e.g. 58"
            />
          </label>

          <label className="block text-sm">
            <span className="font-medium">Typical miss</span>
            <input
              required
              maxLength={160}
              value={typicalMiss}
              onChange={(e) => {
                setTypicalMiss(e.target.value);
                setSaved(false);
              }}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="e.g. tops, slices, chunks"
            />
          </label>
        </div>

        <label className="block text-sm">
          <span className="font-medium">Main goal</span>
          <input
            required
            maxLength={160}
            value={primaryGoal}
            onChange={(e) => {
              setPrimaryGoal(e.target.value);
              setSaved(false);
            }}
            className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
            placeholder="e.g. make better contact and break 50"
          />
        </label>

        <div>
          <label className="block text-sm font-medium">Physical constraints</label>
          <p className="mt-0.5 text-xs text-[var(--color-muted)]">
            Injuries, pain, mobility limits — we will not prescribe moves that fight this.
          </p>
          <textarea
            required={!noLimitations}
            disabled={noLimitations}
            rows={3}
            value={limitations}
            onChange={(e) => {
              setLimitations(e.target.value);
              setSaved(false);
            }}
            className="mt-2 w-full resize-y rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)] disabled:opacity-50"
            placeholder="e.g. Lower back pain — avoid aggressive rotation"
          />
          <label className="mt-3 flex cursor-pointer items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={noLimitations}
              onChange={(e) => {
                setNoLimitations(e.target.checked);
                setSaved(false);
              }}
              className="mt-0.5"
            />
            <span>I don&apos;t have significant physical limitations</span>
          </label>
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <Button
          type="submit"
          disabled={saving || !draftComplete}
          className="w-full sm:w-auto"
          size="lg"
        >
          {saving ? "Saving…" : complete && saved ? "Update profile" : "Save & continue to upload"}
        </Button>
      </form>
    </Card>
  );
}
