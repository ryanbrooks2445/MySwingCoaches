import { ImageResponse } from "next/og";
import { APP_NAME } from "@/lib/brand";

export const runtime = "edge";
export const alt = `${APP_NAME} — AI Golf Swing Analysis`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 72,
          background: "#041712",
          color: "#ffffff",
        }}
      >
        <div style={{ fontSize: 28, color: "#4ade80", letterSpacing: 4, textTransform: "uppercase" }}>
          {APP_NAME}
        </div>
        <div style={{ marginTop: 24, fontSize: 64, fontWeight: 700, lineHeight: 1.1, maxWidth: 900 }}>
          Stop guessing. Know exactly what to practice next.
        </div>
        <div style={{ marginTop: 28, fontSize: 28, color: "rgba(255,255,255,0.7)", maxWidth: 800 }}>
          Upload one swing. Get prioritized fixes, evidence from your film, and drills.
        </div>
      </div>
    ),
    size
  );
}
