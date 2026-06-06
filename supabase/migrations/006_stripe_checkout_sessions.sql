-- Idempotent Stripe Checkout fulfillment log

CREATE TABLE IF NOT EXISTS stripe_checkout_sessions (
  id TEXT PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL DEFAULT 0,
  credits_added INTEGER NOT NULL DEFAULT 1,
  analyses_limit_after INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stripe_checkout_sessions_user_id
  ON stripe_checkout_sessions(user_id);

ALTER TABLE stripe_checkout_sessions ENABLE ROW LEVEL SECURITY;

-- Only service role (webhook) writes; no client policies needed.
