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
├── apps/web/              # Next.js App Router frontend
├── analysis-service/      # FastAPI + OpenCV + Gemini
├── supabase/migrations/   # Postgres schema + RLS + storage
├── packages/shared-types/ # Shared TypeScript types
└── docs/                  # Production TODOs
```

## Setup

### 1. Clone and configure environment

```bash
cd ~/MySwingCoaches
cp .env.example apps/web/.env.local
cp analysis-service/.env.example analysis-service/.env
```

Fill in:

| Variable | Where |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project → Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase project → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase project → Settings → API (server only) |
| `GEMINI_API_KEY` | Google AI Studio |
| `ANALYSIS_SERVICE_URL` | `http://localhost:8001` |
| `ANALYSIS_SERVICE_SECRET` | Shared secret between Next.js and FastAPI |
| `SUPABASE_URL` | Same as `NEXT_PUBLIC_SUPABASE_URL` (analysis-service `.env`) |

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

### 3. Install dependencies

```bash
# Frontend
cd apps/web && npm install

# Analysis service
cd ../../analysis-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run locally

**Terminal 1 — Next.js**

```bash
cd apps/web
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

## Pricing (stub)

Plans are stored in `subscriptions`. UI at `/pricing` updates plan without Stripe. See `docs/PRODUCTION-TODOS.md` for payment integration.

## Disclaimer

All reports include:

> AI-generated swing analysis inspired by common coaching principles. This does not replace in-person instruction from a certified golf professional.

## Known MVP limitations

- Key frames are evenly sampled from the video (not ML phase detection)
- Analysis runs synchronously — long videos may timeout (max 100MB recommended, ~30s)
- Coaching is entirely from Gemini watching your video — not a launch monitor or certified PGA analysis

## License

MIT
