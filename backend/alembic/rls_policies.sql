#ALTER TABLE teams             ENABLE ROW LEVEL SECURITY;
#ALTER TABLE team_memberships  ENABLE ROW LEVEL SECURITY;
#ALTER TABLE team_invitations  ENABLE ROW LEVEL SECURITY;
#ALTER TABLE usage_events      ENABLE ROW LEVEL SECURITY;
#ALTER TABLE support_tickets   ENABLE ROW LEVEL SECURITY;
#ALTER TABLE feature_flags     ENABLE ROW LEVEL SECURITY;

-- =============================================================
-- Phase 1: Drop all existing policies
-- =============================================================

DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT policyname, tablename
    FROM pg_policies
    WHERE schemaname = 'public'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, r.tablename);
  END LOOP;
END;
$$;

-- =============================================================
-- Phase 2: Recreate with (SELECT auth.uid()) wrapper
-- =============================================================

-- teams
CREATE POLICY "teams_select" ON teams FOR SELECT USING (
  id IN (
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid())
  )
);

CREATE POLICY "teams_insert" ON teams FOR INSERT WITH CHECK (
  owner_id = (SELECT auth.uid())
);

CREATE POLICY "teams_update" ON teams FOR UPDATE USING (
  owner_id = (SELECT auth.uid())
  OR id IN (
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

CREATE POLICY "teams_delete" ON teams FOR DELETE USING (
  owner_id = (SELECT auth.uid())
);

-- team_memberships
CREATE POLICY "memberships_select" ON team_memberships FOR SELECT USING (
  team_id IN (
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid())
  )
);

CREATE POLICY "memberships_insert" ON team_memberships FOR INSERT WITH CHECK (
  team_id IN (
    SELECT id FROM teams WHERE owner_id = (SELECT auth.uid())
    UNION
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

CREATE POLICY "memberships_update" ON team_memberships FOR UPDATE USING (
  user_id = (SELECT auth.uid())
  OR team_id IN (
    SELECT id FROM teams WHERE owner_id = (SELECT auth.uid())
    UNION
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

CREATE POLICY "memberships_delete" ON team_memberships FOR DELETE USING (
  user_id = (SELECT auth.uid())
  OR team_id IN (
    SELECT id FROM teams WHERE owner_id = (SELECT auth.uid())
    UNION
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

-- team_invitations
CREATE POLICY "invitations_select" ON team_invitations FOR SELECT USING (
  email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
  OR team_id IN (
    SELECT id FROM teams WHERE owner_id = (SELECT auth.uid())
    UNION
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

CREATE POLICY "invitations_insert" ON team_invitations FOR INSERT WITH CHECK (
  team_id IN (
    SELECT id FROM teams WHERE owner_id = (SELECT auth.uid())
    UNION
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

CREATE POLICY "invitations_update" ON team_invitations FOR UPDATE USING (
  email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
  OR team_id IN (
    SELECT id FROM teams WHERE owner_id = (SELECT auth.uid())
    UNION
    SELECT team_id FROM team_memberships
    WHERE user_id = (SELECT auth.uid()) AND role = 'admin'
  )
);

-- usage_events
CREATE POLICY "usage_own_select" ON usage_events FOR SELECT USING (
  user_id = (SELECT auth.uid())
);

CREATE POLICY "usage_own_insert" ON usage_events FOR INSERT WITH CHECK (
  user_id = (SELECT auth.uid())
);

-- support_tickets
CREATE POLICY "tickets_own" ON support_tickets FOR ALL USING (
  user_id = (SELECT auth.uid())
);

-- feature_flags (read-only for all authenticated users)
CREATE POLICY "flags_select" ON feature_flags FOR SELECT TO authenticated USING (true);