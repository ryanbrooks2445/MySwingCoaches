-- Add swing strengths (positives) to reports
ALTER TABLE swing_reports
  ADD COLUMN IF NOT EXISTS swing_strengths JSONB NOT NULL DEFAULT '[]'::jsonb;
