-- Annual unlimited subscription plan + period tracking (enum must commit before functions)

ALTER TYPE subscription_plan ADD VALUE IF NOT EXISTS 'unlimited_annual';

ALTER TABLE public.subscriptions
  ADD COLUMN IF NOT EXISTS period_end TIMESTAMPTZ;
