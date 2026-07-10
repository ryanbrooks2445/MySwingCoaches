-- Allow upload and analyze before payment; checkout unlocks queued analysis.

ALTER TYPE report_status ADD VALUE IF NOT EXISTS 'awaiting_payment';

CREATE OR REPLACE FUNCTION private.start_queued_analysis(
  p_report_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  report public.swing_reports%ROWTYPE;
BEGIN
  SELECT * INTO report
  FROM public.swing_reports
  WHERE id = p_report_id
    AND user_id = p_user_id
  FOR UPDATE;

  IF NOT FOUND OR report.status <> 'awaiting_payment' THEN
    RETURN FALSE;
  END IF;

  IF NOT private.reserve_analysis_credit(p_user_id, p_report_id) THEN
    RETURN FALSE;
  END IF;

  UPDATE public.swing_reports
  SET status = 'processing',
      error_message = NULL,
      updated_at = NOW()
  WHERE id = p_report_id;

  UPDATE public.swing_videos
  SET status = 'processing',
      updated_at = NOW()
  WHERE id = report.video_id;

  INSERT INTO public.analysis_jobs (report_id, user_id)
  VALUES (p_report_id, p_user_id)
  ON CONFLICT (report_id) DO NOTHING;

  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION private.register_uploaded_swing(
  p_session_id UUID,
  p_user_id UUID
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  upload public.upload_sessions%ROWTYPE;
BEGIN
  SELECT * INTO upload
  FROM public.upload_sessions
  WHERE id = p_session_id
    AND user_id = p_user_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Upload session not found';
  END IF;

  IF upload.status = 'registered' THEN
    RETURN upload.report_id;
  END IF;

  IF upload.status NOT IN ('pending', 'uploaded') OR upload.expires_at < NOW() THEN
    RAISE EXCEPTION 'Upload session is no longer valid';
  END IF;

  INSERT INTO public.swing_videos (
    id, user_id, storage_path, original_filename, mime_type,
    size_bytes, swing_mode, status
  )
  VALUES (
    upload.video_id, upload.user_id, upload.storage_path,
    upload.original_filename, upload.mime_type, upload.size_bytes,
    upload.swing_mode, 'uploaded'
  )
  ON CONFLICT (id) DO NOTHING;

  INSERT INTO public.swing_reports (
    id, user_id, video_id, swing_mode, status
  )
  VALUES (
    upload.report_id, upload.user_id, upload.video_id,
    upload.swing_mode, 'awaiting_payment'
  )
  ON CONFLICT (id) DO NOTHING;

  PERFORM private.start_queued_analysis(upload.report_id, p_user_id);

  UPDATE public.upload_sessions
  SET status = 'registered', updated_at = NOW()
  WHERE id = upload.id;

  RETURN upload.report_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.service_start_queued_analysis(
  p_report_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT private.start_queued_analysis(p_report_id, p_user_id);
$$;

REVOKE ALL ON FUNCTION public.service_start_queued_analysis(UUID, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.service_start_queued_analysis(UUID, UUID)
  TO service_role;
