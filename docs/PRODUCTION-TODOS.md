# Production TODOs

Items still open after launch hardening. Completed Stripe, queue, rate-limit wiring, and core auth/upload flows live in the app — see README deploy checklist.

## Legal (manual)

- [ ] Attorney review of Terms, Privacy, and Refund Policy; remove in-page attorney-review notices after counsel sign-off
- [ ] Enable Supabase Auth leaked-password protection in the dashboard
- [ ] Confirm Supabase Auth email confirmation templates + redirect allow list for production domain

## Infrastructure

- [ ] Configure Upstash Redis env vars in Vercel (required in production)
- [ ] Configure Resend + SUPPORT_INBOX_EMAIL for support alerts
- [ ] Configure Plausible domain (`NEXT_PUBLIC_PLAUSIBLE_DOMAIN`)
- [ ] Configure Sentry DSN (`SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN`) for web + analysis-service
- [ ] Virus scan on uploaded videos
- [ ] Content moderation for storage
- [ ] CDN for swing-frames bucket; retention / lifecycle policies

## Analysis quality

- [ ] Host proprietary drill clips in Supabase `drill-videos` bucket (replace YouTube catalog URLs)
- [ ] Trained swing phase classifier for better key-frame labels
- [ ] FFmpeg transcoding pipeline (normalize fps, resolution, rotation from phone metadata)

## Product

- [ ] Email notifications when analysis completes
- [ ] Supabase Realtime instead of polling on report page
- [ ] Magic link auth
- [ ] Mobile app or PWA optimizations for upload from camera roll
