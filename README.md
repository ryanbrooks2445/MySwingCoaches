# ForeFixed

AI golf swing analysis platform. Upload a swing video and get a Gemini-powered coaching report from full video analysis.

**Architecture:** signed browser upload → durable Supabase job → Cloud Run worker → normalized video + Gemini multimodal coaching → saved report.

## Prerequisites

- Node.js 20+
- Python 3.11+ (3.12 recommended)
- FFmpeg (for OpenCV video codecs)
- [Supabase CLI](https://supabase.com/docs/guides/cli) (optional for local stack)
- Google AI Studio API key ([Gemini](https://aistudio.google.com/apikey))

## Project structure

```
MySwingCoaches/
├── src/                   # Next.js App Router frontend
├── analysis-service/      # FastAPI + OpenCV + Gemini
├── supabase/migrations/   # Postgres schema + RLS + storage
└── docs/                  # Production TODOs
```

## Setup

### 1. Clone and configure environment

```bash
cd ~/MySwingCoaches
cp .env.example .env.local
cp analysis-service/.env.example analysis-service/.env
```

Fill in:

| Variable | Where |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project → Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase project → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase project → Settings → API (server only) |
| `GEMINI_API_KEY` | Google AI Studio; analysis service only |
| `ANALYSIS_SERVICE_SECRET` | Shared secret stored in Cloud Run and Supabase Vault |
| `SUPABASE_URL` | Same project URL; analysis service only |
| `STRIPE_SECRET_KEY` | Stripe secret key for Checkout |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret for `/api/stripe/webhook` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Optional for future Stripe Elements; Checkout redirect does not require it |
| `UPSTASH_REDIS_REST_URL` | Upstash REST endpoint for production rate limits |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash REST token; server only |
| `SENTRY_DSN` | Server error monitoring DSN |
| `ALLOWED_CORS_ORIGINS` | Exact production web origins accepted by Cloud Run |

### 2. Supabase database

Create a project at [supabase.com](https://supabase.com), then:

```bash
# Option A: Supabase CLI
supabase link --project-ref YOUR_PROJECT_REF
supabase db push

# Option B: Manual
# Run supabase/migrations/001_initial_schema.sql in the SQL Editor
```

Storage buckets `swing-videos` and `swing-frames` are created by the migration.

**Sign-up without email confirmation (recommended for dev):** In the [Supabase Dashboard](https://supabase.com/dashboard) → **Authentication** → **Sign In / Providers** → **Email**, disable **Confirm email**. Save. Existing unconfirmed users may still need a one-time SQL confirm in **SQL Editor**:

```sql
UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;
```

### 3. Install dependencies

```bash
# Frontend
npm install

# Analysis service
cd analysis-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run locally

**Terminal 1 — Next.js**

```bash
cd ~/MySwingCoaches
npm run dev
```

**Terminal 2 — Analysis service**

```bash
cd analysis-service
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

Open [http://localhost:3000](http://localhost:3000).

### 5. Test analysis pipeline (no Supabase)

```bash
cd analysis-service
source .venv/bin/activate
python scripts/run_local_analysis.py /path/to/swing.mp4
```

## User flow

1. Sign up / log in (Supabase Auth)
2. Upload MP4 or MOV on `/upload`
3. Browser uploads directly to private Supabase Storage
4. Registration atomically creates the video, report, and analysis job
5. Supabase Cron dispatches queued work to Cloud Run
6. Cloud Run normalizes the phone video, extracts frames, and requests structured Gemini coaching
7. Results persist in Supabase; retries and terminal credit restoration happen without the browser remaining open

## Coach admin

Set a user's role in the database:

```sql
UPDATE profiles SET role = 'coach' WHERE id = 'USER_UUID';
```

Then visit `/coach/reviews`.

## Pricing / Stripe

Plans are stored in `subscriptions`. `/pricing` offers:

- **Per swing** — one-time Checkout (`$19.99` per upload)
- **Unlimited annual** — recurring yearly subscription (`$99/year`, unlimited uploads)

When `STRIPE_SECRET_KEY` is set, `/api/stripe/checkout` creates the appropriate Stripe Checkout session. Stripe must send webhook events to:

```text
https://YOUR_WEB_APP_DOMAIN/api/stripe/webhook
```

Required events:

- `checkout.session.completed` — fulfill per-swing credits and new annual subscriptions
- `invoice.paid` — extend annual subscription `period_end` on renewal
- `customer.subscription.updated` — revoke access on `past_due` / `unpaid` / `canceled`
- `customer.subscription.deleted` — revoke unlimited access

Enable the **Stripe Customer Portal** in the Stripe Dashboard (Settings → Billing → Customer portal) so subscribers can manage/cancel from `/pricing`.

The webhook verifies `STRIPE_WEBHOOK_SECRET`, validates the paid amount and customer for per-swing purchases, then fulfills credits or subscriptions in idempotent database transactions.

## Disclaimer

All reports include:

> AI-generated swing analysis inspired by common coaching principles. This does not replace in-person instruction from a certified golf professional.

## Production deployment

1. Run `npm run check`.
2. Run `npx supabase migration list --linked` and confirm local and remote histories match.
3. Deploy `analysis-service/Dockerfile` to Cloud Run with minimum instances `0`, maximum instances `2`, a 15-minute request timeout, and the analysis-service variables from `.env.example`.
4. Add `analysis_service_url` and `analysis_service_secret` to Supabase Vault. The secret must match Cloud Run.
5. Confirm the `analysis-worker-every-minute` job exists in `cron.job`.
6. Add the web variables from `.env.example` to Vercel Production and Preview.
7. Point Stripe webhooks to `https://YOUR_DOMAIN/api/stripe/webhook` with the events listed in **Pricing / Stripe** above. Enable the Stripe Customer Portal.
8. Run a Stripe test purchase (per-swing and annual), direct phone upload, completed report, duplicate webhook, subscription cancel/revoke, and forced-failure credit restoration before enabling live mode.

Example Vault setup, run in the Supabase SQL editor:

```sql
select vault.create_secret('https://YOUR_CLOUD_RUN_URL', 'analysis_service_url');
select vault.create_secret('YOUR_SHARED_SECRET', 'analysis_service_secret');
```

## MVP boundaries

- This is video-based guidance, not launch-monitor measurement.
- Key frames are sampled checkpoints rather than motion-capture data.
- AI guidance is not a certified PGA lesson or a guaranteed performance result.
- Source videos are private and retained for 30 days; reports remain until account deletion.

## License

MIT
