-- Phase detection metadata for grounded coaching reports
ALTER TABLE public.swing_reports
  ADD COLUMN IF NOT EXISTS phase_map JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS swing_window JSONB DEFAULT NULL;

COMMENT ON COLUMN public.swing_reports.phase_map IS 'Server-verified swing phase frames with confidence scores';
COMMENT ON COLUMN public.swing_reports.swing_window IS 'Detected contiguous swing segment in sampled frames';
