export interface DrillVideoEntry {
  title: string;
  embedUrl: string;
  for: string;
}

/** Client-side catalog mirror — URLs are resolved server-side; this is for fallbacks. */
export const DRILL_CATALOG: Record<string, DrillVideoEntry> = {
  wall_contact: {
    title: "Wall / glute contact drill",
    embedUrl: "https://www.youtube.com/embed/fOpifmb8KZo",
    for: "Early extension, maintaining posture through impact",
  },
  chair_drill: {
    title: "Chair drill — spine angle retention",
    embedUrl: "https://www.youtube.com/embed/5bHGjJ_6Kis",
    for: "Early extension, staying in your angles",
  },
  hip_slide_rotation: {
    title: "Hip slide + rotation sequence",
    embedUrl: "https://www.youtube.com/embed/zEtWHtQR0T0",
    for: "Transition, clearing hips without thrusting at the ball",
  },
  back_to_target: {
    title: "Back-to-target turn",
    embedUrl: "https://www.youtube.com/embed/iwbHIX3IlhA",
    for: "Over-the-top, shoulders spinning open too early",
  },
  setup_posture: {
    title: "Athletic setup & posture",
    embedUrl: "https://www.youtube.com/embed/5bHGjJ_6Kis",
    for: "Address position, hip hinge, balance",
  },
  alignment_stick_shallow: {
    title: "Shallowing with alignment stick",
    embedUrl: "https://www.youtube.com/embed/zEtWHtQR0T0",
    for: "Steep downswing, over-the-top path",
  },
  feet_together: {
    title: "Feet-together balance swings",
    embedUrl: "https://www.youtube.com/embed/fOpifmb8KZo",
    for: "Balance, tempo, centered rotation",
  },
  slow_motion_reps: {
    title: "Slow-motion rehearsal swings",
    embedUrl: "https://www.youtube.com/embed/iwbHIX3IlhA",
    for: "Building a new feel at half speed",
  },
  generic_feel: {
    title: "Range feel rehearsal",
    embedUrl: "https://www.youtube.com/embed/fOpifmb8KZo",
    for: "General kinesthetic practice",
  },
};

export function resolveDrillVideoUrl(
  videoUrl: string | null | undefined,
  videoSlug: string | null | undefined,
  stepType: string
): { url: string; title: string } | null {
  if (videoUrl) {
    return { url: videoUrl, title: "Drill demonstration" };
  }
  const slug =
    videoSlug ??
    (stepType === "constraint_drill"
      ? "wall_contact"
      : stepType === "visual_cue"
        ? "back_to_target"
        : "setup_posture");
  const entry = DRILL_CATALOG[slug] ?? DRILL_CATALOG.generic_feel;
  return { url: entry.embedUrl, title: entry.title };
}
