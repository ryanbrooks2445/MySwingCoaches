-- Launch hardening: durable jobs, atomic credits, strict RLS, support, and retention.

CREATE SCHEMA IF NOT EXISTS private;
REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated;

ALTER TABLE public.swing_reports
  ADD COLUMN IF NOT EXISTS error_code TEXT,
  ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS source_video_deleted_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS public.analysis_credit_reservations (
  report_id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'reserved'
    CHECK (status IN ('reserved', 'completed', 'restored')),
  restore_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  restored_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.upload_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  report_id UUID NOT NULL UNIQUE,
  video_id UUID NOT NULL UNIQUE,
  storage_path TEXT NOT NULL UNIQUE,
  original_filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 104857600),
  swing_mode swing_mode NOT NULL DEFAULT 'full_swing',
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'uploaded', 'registered', 'expired', 'failed')),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 minutes'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.analysis_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL UNIQUE REFERENCES public.swing_reports(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'retry', 'completed', 'failed')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 3),
  available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  locked_at TIMESTAMPTZ,
  locked_by TEXT,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_ready
  ON public.analysis_jobs (status, available_at)
  WHERE status IN ('queued', 'retry');

CREATE TABLE IF NOT EXISTS public.support_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 320),
  subject TEXT NOT NULL CHECK (length(subject) BETWEEN 3 AND 160),
  message TEXT NOT NULL CHECK (length(message) BETWEEN 10 AND 4000),
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.account_deletion_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id_hash TEXT NOT NULL,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'requested'
    CHECK (status IN ('requested', 'completed', 'failed')),
  error_message TEXT
);

ALTER TABLE public.analysis_credit_reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.support_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.account_deletion_audit ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users update own subscription" ON public.subscriptions;
DROP POLICY IF EXISTS "Users read own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users read own subscription" ON public.subscriptions;
DROP POLICY IF EXISTS "Users read own videos" ON public.swing_videos;
DROP POLICY IF EXISTS "Users insert own videos" ON public.swing_videos;
DROP POLICY IF EXISTS "Users update own videos" ON public.swing_videos;
DROP POLICY IF EXISTS "Users read own reports" ON public.swing_reports;
DROP POLICY IF EXISTS "Users insert own reports" ON public.swing_reports;
DROP POLICY IF EXISTS "Users read own metrics" ON public.swing_metrics;
DROP POLICY IF EXISTS "Users read own issues" ON public.swing_issues;
DROP POLICY IF EXISTS "Users read own drills" ON public.drill_recommendations;
DROP POLICY IF EXISTS "Users read own coach reviews" ON public.coach_reviews;
DROP POLICY IF EXISTS "Users request coach review" ON public.coach_reviews;
DROP POLICY IF EXISTS "Coaches read all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Coaches read all videos" ON public.swing_videos;
DROP POLICY IF EXISTS "Coaches read all reports" ON public.swing_reports;
DROP POLICY IF EXISTS "Coaches manage reviews" ON public.coach_reviews;

REVOKE UPDATE ON TABLE public.subscriptions FROM authenticated;
REVOKE UPDATE ON TABLE public.profiles FROM authenticated;

CREATE OR REPLACE FUNCTION private.is_coach_or_admin()
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.profiles
    WHERE id = (SELECT auth.uid())
      AND role IN ('coach', 'admin')
  );
$$;

REVOKE ALL ON FUNCTION private.is_coach_or_admin() FROM PUBLIC, anon, authenticated;

CREATE POLICY "Users read own profile"
  ON public.profiles FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = id);

CREATE POLICY "Coaches read profiles"
  ON public.profiles FOR SELECT TO authenticated
  USING ((SELECT private.is_coach_or_admin()));

CREATE POLICY "Users read own subscription"
  ON public.subscriptions FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own videos"
  ON public.swing_videos FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Coaches read videos"
  ON public.swing_videos FOR SELECT TO authenticated
  USING ((SELECT private.is_coach_or_admin()));

CREATE POLICY "Users read own reports"
  ON public.swing_reports FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Coaches read reports"
  ON public.swing_reports FOR SELECT TO authenticated
  USING ((SELECT private.is_coach_or_admin()));

CREATE POLICY "Users read own metrics"
  ON public.swing_metrics FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own issues"
  ON public.swing_issues FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own drills"
  ON public.drill_recommendations FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own coach reviews"
  ON public.coach_reviews FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Coaches manage reviews"
  ON public.coach_reviews FOR ALL TO authenticated
  USING ((SELECT private.is_coach_or_admin()))
  WITH CHECK ((SELECT private.is_coach_or_admin()));

CREATE POLICY "Users read own upload sessions"
  ON public.upload_sessions FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own analysis jobs"
  ON public.analysis_jobs FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own credit reservations"
  ON public.analysis_credit_reservations FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users create support requests"
  ON public.support_requests FOR INSERT TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users read own support requests"
  ON public.support_requests FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE OR REPLACE FUNCTION private.fulfill_checkout_session(
  p_session_id TEXT,
  p_user_id UUID,
  p_amount_cents INTEGER
)
RETURNS TABLE(applied BOOLEAN, analyses_limit INTEGER)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  inserted_count INTEGER;
BEGIN
  INSERT INTO public.stripe_checkout_sessions (
    id, user_id, amount_cents, credits_added
  )
  VALUES (p_session_id, p_user_id, p_amount_cents, 1)
  ON CONFLICT (id) DO NOTHING;

  GET DIAGNOSTICS inserted_count = ROW_COUNT;

  IF inserted_count = 0 THEN
    RETURN QUERY
      SELECT FALSE, s.analyses_limit
      FROM public.subscriptions s
      WHERE s.user_id = p_user_id;
    RETURN;
  END IF;

  UPDATE public.subscriptions
  SET analyses_limit = public.subscriptions.analyses_limit + 1,
      status = 'active',
      updated_at = NOW()
  WHERE user_id = p_user_id
  RETURNING public.subscriptions.analyses_limit
  INTO analyses_limit;

  UPDATE public.stripe_checkout_sessions
  SET analyses_limit_after = analyses_limit
  WHERE id = p_session_id;

  RETURN QUERY SELECT TRUE, analyses_limit;
END;
$$;

CREATE OR REPLACE FUNCTION private.reserve_analysis_credit(
  p_user_id UUID,
  p_report_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  changed INTEGER;
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.analysis_credit_reservations
    WHERE report_id = p_report_id
  ) THEN
    RETURN TRUE;
  END IF;

  UPDATE public.subscriptions
  SET analyses_used = analyses_used + 1,
      updated_at = NOW()
  WHERE user_id = p_user_id
    AND (analyses_limit = -1 OR analyses_used < analyses_limit);

  GET DIAGNOSTICS changed = ROW_COUNT;
  IF changed = 0 THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.analysis_credit_reservations (report_id, user_id)
  VALUES (p_report_id, p_user_id);
  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION private.restore_analysis_credit(
  p_report_id UUID,
  p_reason TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  reservation public.analysis_credit_reservations%ROWTYPE;
BEGIN
  SELECT * INTO reservation
  FROM public.analysis_credit_reservations
  WHERE report_id = p_report_id
  FOR UPDATE;

  IF NOT FOUND OR reservation.status <> 'reserved' THEN
    RETURN FALSE;
  END IF;

  UPDATE public.analysis_credit_reservations
  SET status = 'restored',
      restore_reason = left(p_reason, 500),
      restored_at = NOW()
  WHERE report_id = p_report_id;

  UPDATE public.subscriptions
  SET analyses_used = GREATEST(0, analyses_used - 1),
      updated_at = NOW()
  WHERE user_id = reservation.user_id
    AND analyses_limit <> -1;

  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION private.complete_analysis(p_report_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  changed INTEGER;
BEGIN
  UPDATE public.analysis_credit_reservations
  SET status = 'completed',
      completed_at = NOW()
  WHERE report_id = p_report_id
    AND status = 'reserved';
  GET DIAGNOSTICS changed = ROW_COUNT;
  RETURN changed = 1;
END;
$$;

CREATE OR REPLACE FUNCTION private.claim_analysis_jobs(
  p_worker_id TEXT,
  p_limit INTEGER DEFAULT 1
)
RETURNS SETOF public.analysis_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  RETURN QUERY
  WITH candidates AS (
    SELECT id
    FROM public.analysis_jobs
    WHERE status IN ('queued', 'retry')
      AND available_at <= NOW()
      AND attempts < 3
    ORDER BY available_at, created_at
    FOR UPDATE SKIP LOCKED
    LIMIT GREATEST(1, LEAST(p_limit, 10))
  )
  UPDATE public.analysis_jobs j
  SET status = 'running',
      attempts = attempts + 1,
      locked_at = NOW(),
      locked_by = p_worker_id,
      updated_at = NOW()
  FROM candidates
  WHERE j.id = candidates.id
  RETURNING j.*;
END;
$$;

CREATE OR REPLACE FUNCTION private.cleanup_expired_uploads()
RETURNS TABLE(storage_path TEXT, report_id UUID)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  RETURN QUERY
  WITH expired AS (
    UPDATE public.upload_sessions
    SET status = 'expired', updated_at = NOW()
    WHERE status IN ('pending', 'uploaded')
      AND expires_at < NOW()
    RETURNING public.upload_sessions.storage_path, public.upload_sessions.report_id
  )
  SELECT expired.storage_path, expired.report_id FROM expired;
END;
$$;

CREATE OR REPLACE FUNCTION private.source_videos_due_for_deletion()
RETURNS TABLE(video_id UUID, storage_path TEXT, report_id UUID)
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT v.id, v.storage_path, r.id
  FROM public.swing_videos v
  JOIN public.swing_reports r ON r.video_id = v.id
  WHERE v.created_at < NOW() - INTERVAL '30 days'
    AND r.source_video_deleted_at IS NULL
    AND r.status IN ('ready', 'failed');
$$;

CREATE OR REPLACE FUNCTION public.service_fulfill_checkout_session(
  p_session_id TEXT, p_user_id UUID, p_amount_cents INTEGER
)
RETURNS TABLE(applied BOOLEAN, analyses_limit INTEGER)
LANGUAGE sql SECURITY DEFINER SET search_path = ''
AS $$ SELECT * FROM private.fulfill_checkout_session(p_session_id, p_user_id, p_amount_cents); $$;

CREATE OR REPLACE FUNCTION public.service_reserve_analysis_credit(
  p_user_id UUID, p_report_id UUID
)
RETURNS BOOLEAN
LANGUAGE sql SECURITY DEFINER SET search_path = ''
AS $$ SELECT private.reserve_analysis_credit(p_user_id, p_report_id); $$;

CREATE OR REPLACE FUNCTION public.service_restore_analysis_credit(
  p_report_id UUID, p_reason TEXT
)
RETURNS BOOLEAN
LANGUAGE sql SECURITY DEFINER SET search_path = ''
AS $$ SELECT private.restore_analysis_credit(p_report_id, p_reason); $$;

CREATE OR REPLACE FUNCTION public.service_complete_analysis(p_report_id UUID)
RETURNS BOOLEAN
LANGUAGE sql SECURITY DEFINER SET search_path = ''
AS $$ SELECT private.complete_analysis(p_report_id); $$;

CREATE OR REPLACE FUNCTION public.service_claim_analysis_jobs(
  p_worker_id TEXT, p_limit INTEGER DEFAULT 1
)
RETURNS SETOF public.analysis_jobs
LANGUAGE sql SECURITY DEFINER SET search_path = ''
AS $$ SELECT * FROM private.claim_analysis_jobs(p_worker_id, p_limit); $$;

REVOKE ALL ON FUNCTION public.service_fulfill_checkout_session(TEXT, UUID, INTEGER) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.service_reserve_analysis_credit(UUID, UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.service_restore_analysis_credit(UUID, TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.service_complete_analysis(UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.service_claim_analysis_jobs(TEXT, INTEGER) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.service_fulfill_checkout_session(TEXT, UUID, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION public.service_reserve_analysis_credit(UUID, UUID) TO service_role;
GRANT EXECUTE ON FUNCTION public.service_restore_analysis_credit(UUID, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.service_complete_analysis(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION public.service_claim_analysis_jobs(TEXT, INTEGER) TO service_role;

REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.is_coach_or_admin() FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;
