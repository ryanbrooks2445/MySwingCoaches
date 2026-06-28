-- Harden swing-videos storage: uploads only via credit-gated signed URL (service role).
-- Direct authenticated INSERT/UPDATE allowed storage fill without credit reservation.

DROP POLICY IF EXISTS "Users upload own swing videos" ON storage.objects;
DROP POLICY IF EXISTS "Users update own swing videos" ON storage.objects;

-- Coach storage read policy referenced public.is_coach_or_admin(), revoked from clients in 008.
-- Coach APIs use service role for video access instead.
DROP POLICY IF EXISTS "Coaches read swing videos" ON storage.objects;

-- Keep "Users read own swing videos" SELECT for client playback if needed.
-- swing-frames writes remain service-role only (no client INSERT policy).
