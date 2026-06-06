-- Golfer physical profile for pain-safe, age-appropriate coaching

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS age INTEGER CHECK (age IS NULL OR (age >= 5 AND age <= 120)),
  ADD COLUMN IF NOT EXISTS years_playing INTEGER CHECK (years_playing IS NULL OR (years_playing >= 0 AND years_playing <= 100)),
  ADD COLUMN IF NOT EXISTS physical_limitations TEXT;
