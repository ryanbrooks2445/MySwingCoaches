import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const DISCLAIMER =
  "AI-generated swing analysis inspired by common coaching principles. This does not replace in-person instruction from a certified golf professional.";

export const MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024;
export const MAX_VIDEO_DURATION_SEC = 30;
export const ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime"];
