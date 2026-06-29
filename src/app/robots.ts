import type { MetadataRoute } from "next";

const baseUrl = "https://forefixed.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/account", "/coach", "/dashboard", "/progress", "/swings", "/upload"],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
