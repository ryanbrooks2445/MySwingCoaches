import type { MetadataRoute } from "next";

const baseUrl = "https://forefixed.com";

const publicRoutes = [
  "",
  "/pricing",
  "/example",
  "/signup",
  "/login",
  "/reset-password",
  "/support",
  "/contact",
  "/terms",
  "/privacy",
  "/refund-policy",
  "/video-retention",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return publicRoutes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: now,
  }));
}
