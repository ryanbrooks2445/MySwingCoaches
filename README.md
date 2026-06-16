# MySwingCoaches

AI golf swing analysis platform. Upload a swing video and get a Gemini-powered coaching report from full video analysis.

**Architecture:** Video upload → OpenCV frame extraction → **Gemini multimodal video coaching** → dashboard.

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
| `GEMINI_API_KEY` | Google AI Studio |
| `ANALYSIS_SERVICE_URL` | `http://localhost:8001` locally; deployed FastAPI URL in production |
| `ANALYSIS_SERVICE_SECRET` | Shared secret between Next.js and FastAPI |
| `SUPABASE_URL` | Same as `NEXT_PUBLIC_SUPABASE_URL` (analysis-service `.env`) |
| `STRIPE_SECRET_KEY` | Stripe secret key for Checkout |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret for `/api/stripe/webhook` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Optional for future Stripe Elements; Checkout redirect does not require it |
| `ENABLE_DEV_CREDIT_STUB` | Local-only fallback for testing credits without Stripe; keep `false` in production |

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
3. Video stored in Supabase Storage; `swing_reports` created with status `processing`
4. Next.js calls FastAPI `/analyze` with signed video URL
5. FastAPI: OpenCV frames → Gemini video coaching JSON
6. Results persisted to Supabase; user views report at `/swings/[id]`

## Coach admin

Set a user's role in the database:

```sql
UPDATE profiles SET role = 'coach' WHERE id = 'USER_UUID';
```

Then visit `/coach/reviews`.

## Pricing / Stripe

Plans are stored in `subscriptions`. `/pricing` creates a Stripe Checkout session when `STRIPE_SECRET_KEY` is set. The app creates the one-analysis line item dynamically from the current intro/standard price in `src/lib/pricing.ts`. Stripe must send `checkout.session.completed` events to:

```text
https://YOUR_WEB_APP_DOMAIN/api/stripe/webhook
```

The webhook verifies `STRIPE_WEBHOOK_SECRET`, records the Stripe session idempotently in `stripe_checkout_sessions`, and adds one prepaid analysis credit. For local-only testing without Stripe, set `ENABLE_DEV_CREDIT_STUB=true`; production blocks the stub routes.

## Disclaimer

All reports include:

> AI-generated swing analysis inspired by common coaching principles. This does not replace in-person instruction from a certified golf professional.

## Known MVP limitations

- Key frames are evenly sampled from the video (not ML phase detection)
- Analysis runs synchronously — long videos may timeout (max 100MB recommended, ~30s)
- Coaching is entirely from Gemini watching your video — not a launch monitor or certified PGA analysis

## License

MIT
