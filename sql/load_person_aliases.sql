-- ================================================================
-- LOAD PERSON ALIASES TABLE
-- Name variant matching for donor deduplication
-- ================================================================

-- Create person_aliases table
CREATE TABLE IF NOT EXISTS person_aliases (
  alias_name TEXT PRIMARY KEY,
  canonical_name TEXT NOT NULL,
  master_person_id UUID,
  match_type TEXT NOT NULL,
  confidence NUMERIC(3,2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_person_aliases_canonical ON person_aliases(canonical_name);
CREATE INDEX IF NOT EXISTS idx_person_aliases_confidence ON person_aliases(confidence DESC);

-- Insert sample aliases for "Ed Broyhill" (James Edgar Broyhill)
-- Add your own canonical names and aliases as needed
INSERT INTO person_aliases (alias_name, canonical_name, match_type, confidence) VALUES
-- PREFERRED
('ED BROYHILL', 'James Edgar Broyhill', 'PREFERRED', 1.00),
-- FULL LEGAL VARIANTS
('JAMES EDGAR BROYHILL', 'James Edgar Broyhill', 'FULL_LEGAL', 1.00),
('JAMES (ED) EDGAR BROYHILL', 'James Edgar Broyhill', 'FULL_LEGAL_NICK', 1.00),
('JAMES (ED) BROYHILL', 'James Edgar Broyhill', 'FIRST_NICK_LAST', 1.00),
('JAMES ED BROYHILL', 'James Edgar Broyhill', 'NICK_VARIANT', 0.98),
-- FIRST + MIDDLE INITIAL
('JAMES E BROYHILL', 'James Edgar Broyhill', 'FIRST_MIDINIT', 0.98),
('JAMES E. BROYHILL', 'James Edgar Broyhill', 'FIRST_MIDINIT_DOT', 0.98),
-- FIRST INITIAL + MIDDLE
('J EDGAR BROYHILL', 'James Edgar Broyhill', 'FIRSTINIT_MIDDLE', 0.95),
('J. EDGAR BROYHILL', 'James Edgar Broyhill', 'FIRSTINIT_DOT_MIDDLE', 0.95),
-- MIDDLE AS FIRST
('EDGAR BROYHILL', 'James Edgar Broyhill', 'MIDDLE_AS_FIRST', 0.95),
-- EDWARD/EDDIE VARIANTS
('EDWARD BROYHILL', 'James Edgar Broyhill', 'NICK_FORMAL', 0.92),
('EDDIE BROYHILL', 'James Edgar Broyhill', 'NICK_DIMINUTIVE', 0.90),
-- FIRST INITIAL ONLY
('J BROYHILL', 'James Edgar Broyhill', 'FIRSTINIT_ONLY', 0.75),
('J. BROYHILL', 'James Edgar Broyhill', 'FIRSTINIT_DOT_ONLY', 0.75),
-- FIRST + LAST
('JAMES BROYHILL', 'James Edgar Broyhill', 'FIRST_LAST', 0.85),
-- LAST, FIRST format
('BROYHILL, JAMES EDGAR', 'James Edgar Broyhill', 'LAST_FIRST_MIDDLE', 1.00),
('BROYHILL, ED', 'James Edgar Broyhill', 'LAST_NICK', 1.00),
('BROYHILL, JAMES', 'James Edgar Broyhill', 'LAST_FIRST', 0.85)
ON CONFLICT (alias_name) DO NOTHING;

-- View to help match donors
CREATE OR REPLACE VIEW v_donor_alias_matches AS
SELECT 
  d.id,
  d.donor_name,
  pa.canonical_name,
  pa.match_type,
  pa.confidence
FROM nc_boe_donations_raw d
LEFT JOIN person_aliases pa ON UPPER(TRIM(d.donor_name)) = pa.alias_name;
