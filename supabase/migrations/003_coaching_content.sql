-- Coaching blueprint (3-part architecture, no scores)
ALTER TABLE swing_reports
  ADD COLUMN IF NOT EXISTS coaching_content JSONB;
