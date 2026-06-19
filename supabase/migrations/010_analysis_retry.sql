-- Requeue a failed analysis using the retained source video and one available credit.

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
    AND (analyses_limit = -1 OR analyses_used < analyses_limit);
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

CREATE OR REPLACE FUNCTION public.service_requeue_analysis(
  p_report_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT private.requeue_analysis(p_report_id, p_user_id);
$$;

REVOKE ALL ON FUNCTION public.service_requeue_analysis(UUID, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.service_requeue_analysis(UUID, UUID)
  TO service_role;
