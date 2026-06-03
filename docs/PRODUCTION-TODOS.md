# Production TODOs

Items intentionally stubbed or simplified in the MVP.

## Payments

- [ ] Stripe Checkout for Player ($19/mo) and Serious Golfer ($49/mo) plans
- [ ] Stripe webhooks to sync `subscriptions` status, period, and usage resets
- [ ] Coach Review add-on as Stripe line item or one-time payment

## Infrastructure

- [ ] Background job queue (Inngest, Trigger.dev, or Supabase Edge Functions + queue) instead of synchronous FastAPI call from Next.js
- [ ] Webhook auth + idempotency keys for `/analyze`
- [ ] Rate limiting (Upstash Redis) on upload and analyze endpoints
- [ ] Horizontal scaling for analysis workers; optional GPU for MediaPipe
- [ ] CDN for swing-frames bucket; retention / lifecycle policies

## Analysis quality

- [ ] Replace checkpoint heuristics with trained phase classifier or club-head tracking
- [ ] Real pro swing model library (replace placeholder images in `ComparisonPanel`)
- [ ] Multimodal Gemini: pass key frame bytes for visual reasoning
- [ ] FFmpeg transcoding pipeline (normalize fps, resolution, rotation from phone metadata)
- [ ] Camera-angle calibration and multi-view fusion
- [ ] Confidence thresholds — skip report sections when pose visibility is low

## Security & compliance

- [ ] Virus scan on uploaded videos
- [ ] Content moderation for storage
- [ ] Audit logging for service-role operations
- [ ] Legal review of coaching claims and disclaimer copy

## Observability

- [ ] Sentry (frontend + FastAPI)
- [ ] Structured logging with analysis_id correlation
- [ ] Metrics: analysis duration, Gemini latency, failure rates

## Product

- [ ] Email notifications when analysis completes
- [ ] Supabase Realtime instead of polling on report page
- [ ] Magic link auth
- [ ] Mobile app or PWA optimizations for upload from camera roll
