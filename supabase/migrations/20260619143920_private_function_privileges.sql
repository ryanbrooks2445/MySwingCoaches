-- PostgreSQL grants EXECUTE on new functions to PUBLIC by default.
-- Keep implementation functions unreachable even if later migrations recreate them.
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA private FROM PUBLIC, anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA private
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

ALTER DEFAULT PRIVILEGES IN SCHEMA private
  REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated;
