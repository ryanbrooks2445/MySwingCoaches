-- Transactional upload registration and durable analysis job creation.

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

  IF NOT EXISTS (
    SELECT 1
    FROM public.analysis_credit_reservations r
    WHERE r.report_id = upload.report_id
      AND r.user_id = p_user_id
      AND r.status = 'reserved'
  ) THEN
    RAISE EXCEPTION 'Analysis credit is not reserved';
  END IF;

  INSERT INTO public.swing_videos (
    id, user_id, storage_path, original_filename, mime_type,
    size_bytes, swing_mode, status
  )
  VALUES (
    upload.video_id, upload.user_id, upload.storage_path,
    upload.original_filename, upload.mime_type, upload.size_bytes,
    upload.swing_mode, 'processing'
  )
  ON CONFLICT (id) DO NOTHING;

  INSERT INTO public.swing_reports (
    id, user_id, video_id, swing_mode, status
  )
  VALUES (
    upload.report_id, upload.user_id, upload.video_id,
    upload.swing_mode, 'processing'
  )
  ON CONFLICT (id) DO NOTHING;

  INSERT INTO public.analysis_jobs (report_id, user_id)
  VALUES (upload.report_id, upload.user_id)
  ON CONFLICT (report_id) DO NOTHING;

  UPDATE public.upload_sessions
  SET status = 'registered', updated_at = NOW()
  WHERE id = upload.id;

  RETURN upload.report_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.service_register_uploaded_swing(
  p_session_id UUID,
  p_user_id UUID
)
RETURNS UUID
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT private.register_uploaded_swing(p_session_id, p_user_id);
$$;

REVOKE ALL ON FUNCTION public.service_register_uploaded_swing(UUID, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.service_register_uploaded_swing(UUID, UUID)
  TO service_role;
