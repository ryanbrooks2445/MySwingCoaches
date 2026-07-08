-- Annual unlimited subscription RPCs and period-aware credit gating

CREATE OR REPLACE FUNCTION private.fulfill_subscription(
  p_user_id UUID,
  p_stripe_subscription_id TEXT,
  p_period_end TIMESTAMPTZ,
  p_plan subscription_plan DEFAULT 'unlimited_annual'
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  UPDATE public.subscriptions
  SET plan = p_plan,
      analyses_limit = -1,
      status = 'active',
      stripe_subscription_id = p_stripe_subscription_id,
      period_start = NOW(),
      period_end = p_period_end,
      updated_at = NOW()
  WHERE user_id = p_user_id;

  RETURN FOUND;
END;
$$;

CREATE OR REPLACE FUNCTION private.revoke_subscription(
  p_stripe_subscription_id TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  UPDATE public.subscriptions
  SET plan = 'free',
      analyses_limit = 0,
      status = 'canceled',
      stripe_subscription_id = NULL,
      period_end = NULL,
      updated_at = NOW()
  WHERE stripe_subscription_id = p_stripe_subscription_id;

  RETURN FOUND;
END;
$$;

CREATE OR REPLACE FUNCTION private.extend_subscription_period(
  p_stripe_subscription_id TEXT,
  p_period_end TIMESTAMPTZ
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  UPDATE public.subscriptions
  SET period_end = p_period_end,
      status = 'active',
      updated_at = NOW()
  WHERE stripe_subscription_id = p_stripe_subscription_id
    AND analyses_limit = -1;

  RETURN FOUND;
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
    AND (
      (
        analyses_limit = -1
        AND status = 'active'
        AND (period_end IS NULL OR period_end > NOW())
      )
      OR (analyses_limit <> -1 AND analyses_used < analyses_limit)
    );

  GET DIAGNOSTICS changed = ROW_COUNT;
  IF changed = 0 THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.analysis_credit_reservations (report_id, user_id)
  VALUES (p_report_id, p_user_id);
  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION private.requeue_analysis(
  p_report_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  reservation public.analysis_credit_reservations%ROWTYPE;
  changed INTEGER;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.swing_reports
    WHERE id = p_report_id
      AND user_id = p_user_id
      AND status = 'failed'
      AND source_video_deleted_at IS NULL
  ) THEN
    RETURN FALSE;
  END IF;

  SELECT * INTO reservation
  FROM public.analysis_credit_reservations
  WHERE report_id = p_report_id
    AND user_id = p_user_id
  FOR UPDATE;

  IF NOT FOUND OR reservation.status <> 'restored' THEN
    RETURN FALSE;
  END IF;

  UPDATE public.subscriptions
  SET analyses_used = analyses_used + 1,
      updated_at = NOW()
  WHERE user_id = p_user_id
    AND (
      (
        analyses_limit = -1
        AND status = 'active'
        AND (period_end IS NULL OR period_end > NOW())
      )
      OR (analyses_limit <> -1 AND analyses_used < analyses_limit)
    );
  GET DIAGNOSTICS changed = ROW_COUNT;
  IF changed = 0 THEN
    RETURN FALSE;
  END IF;

  UPDATE public.analysis_credit_reservations
  SET status = 'reserved',
      restore_reason = NULL,
      restored_at = NULL,
      completed_at = NULL
  WHERE report_id = p_report_id;

  UPDATE public.swing_reports
  SET status = 'processing',
      error_code = NULL,
      error_message = NULL,
      ai_narrative_available = TRUE,
      attempt_count = 0,
      updated_at = NOW()
  WHERE id = p_report_id;

  UPDATE public.swing_videos
  SET status = 'processing', updated_at = NOW()
  WHERE id = (SELECT video_id FROM public.swing_reports WHERE id = p_report_id);

  UPDATE public.analysis_jobs
  SET status = 'queued',
      attempts = 0,
      available_at = NOW(),
      locked_at = NULL,
      locked_by = NULL,
      last_error = NULL,
      updated_at = NOW()
  WHERE report_id = p_report_id;

  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION public.service_fulfill_subscription(
  p_user_id UUID,
  p_stripe_subscription_id TEXT,
  p_period_end TIMESTAMPTZ,
  p_plan subscription_plan DEFAULT 'unlimited_annual'
)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT private.fulfill_subscription(
    p_user_id,
    p_stripe_subscription_id,
    p_period_end,
    p_plan
  );
$$;

CREATE OR REPLACE FUNCTION public.service_revoke_subscription(
  p_stripe_subscription_id TEXT
)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$ SELECT private.revoke_subscription(p_stripe_subscription_id); $$;

CREATE OR REPLACE FUNCTION public.service_extend_subscription_period(
  p_stripe_subscription_id TEXT,
  p_period_end TIMESTAMPTZ
)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT private.extend_subscription_period(p_stripe_subscription_id, p_period_end);
$$;

REVOKE ALL ON FUNCTION public.service_fulfill_subscription(UUID, TEXT, TIMESTAMPTZ, subscription_plan) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.service_revoke_subscription(TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.service_extend_subscription_period(TEXT, TIMESTAMPTZ) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.service_fulfill_subscription(UUID, TEXT, TIMESTAMPTZ, subscription_plan) TO service_role;
GRANT EXECUTE ON FUNCTION public.service_revoke_subscription(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.service_extend_subscription_period(TEXT, TIMESTAMPTZ) TO service_role;
