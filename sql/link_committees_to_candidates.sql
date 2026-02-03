-- ============================================================================
-- Committee to Candidate Linking Pipeline
-- ============================================================================
-- Links political committees to candidates using county + fuzzy name matching
-- Enriches donation records with candidate_id for direct candidate analysis
-- ============================================================================

-- Step 1: Enable fuzzy matching extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Step 2: Create the committee-candidate link table
CREATE TABLE IF NOT EXISTS committee_candidates (
  id BIGSERIAL PRIMARY KEY,
  committee_id TEXT NOT NULL,
  committee_name TEXT,
  candidate_id BIGINT REFERENCES ncsbe_candidates(id),
  match_type TEXT,
  confidence NUMERIC(4,3),
  county_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(committee_id)
);

-- Step 3: Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_committee_candidates_committee_id 
  ON committee_candidates(committee_id);
CREATE INDEX IF NOT EXISTS idx_committee_candidates_candidate_id 
  ON committee_candidates(candidate_id);

-- Step 4: Match committees to candidates using county + fuzzy name
-- Match criteria:
--   1. Same county_name (localized matching)
--   2. Similarity > 0.85 between committee_name and name_on_ballot
INSERT INTO committee_candidates (
  committee_id,
  committee_name,
  candidate_id,
  match_type,
  confidence,
  county_name,
  created_at
)
SELECT DISTINCT ON (c.committee_id)
  c.committee_id,
  c.committee_name,
  can.id AS candidate_id,
  'county+fuzzy_name' AS match_type,
  similarity(LOWER(c.committee_name), LOWER(can.name_on_ballot)) AS confidence,
  c.county_name,
  now()
FROM nc_committee_file c
JOIN ncsbe_candidates can
  ON LOWER(TRIM(c.county_name)) = LOWER(TRIM(can.county_name))
  AND similarity(LOWER(c.committee_name), LOWER(can.name_on_ballot)) > 0.85
WHERE NOT EXISTS (
  SELECT 1 FROM committee_candidates cc
  WHERE cc.committee_id = c.committee_id
)
ORDER BY c.committee_id, 
  similarity(LOWER(c.committee_name), LOWER(can.name_on_ballot)) DESC;

-- Step 5: Add candidate_id column to donations table if not exists
ALTER TABLE nc_boe_donations_raw
ADD COLUMN IF NOT EXISTS candidate_id BIGINT;

-- Step 6: Enrich donor records with matched candidate_id
UPDATE nc_boe_donations_raw d
SET candidate_id = cc.candidate_id
FROM committee_candidates cc
WHERE d.committee_id = cc.committee_id
  AND d.candidate_id IS NULL;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- View: Check match quality
CREATE OR REPLACE VIEW v_committee_candidate_matches AS
SELECT 
  cc.committee_id,
  cc.committee_name,
  cc.candidate_id,
  can.name_on_ballot AS candidate_name,
  can.party,
  can.contest_name,
  cc.county_name,
  cc.confidence,
  cc.match_type
FROM committee_candidates cc
JOIN ncsbe_candidates can ON cc.candidate_id = can.id
ORDER BY cc.confidence DESC;

-- View: Unmatched committees (for review)
CREATE OR REPLACE VIEW v_unmatched_committees AS
SELECT 
  c.committee_id,
  c.committee_name,
  c.county_name,
  c.treasurer_name,
  c.street_line_1,
  c.city,
  c.zip_code
FROM nc_committee_file c
WHERE NOT EXISTS (
  SELECT 1 FROM committee_candidates cc
  WHERE cc.committee_id = c.committee_id
);

-- View: Donations with candidate info
CREATE OR REPLACE VIEW v_donations_with_candidates AS
SELECT 
  d.id AS donation_id,
  d.donor_name,
  d.amount,
  d.contribution_date,
  d.committee_id,
  cc.committee_name,
  d.candidate_id,
  can.name_on_ballot AS candidate_name,
  can.party,
  can.contest_name
FROM nc_boe_donations_raw d
LEFT JOIN committee_candidates cc ON d.committee_id = cc.committee_id
LEFT JOIN ncsbe_candidates can ON d.candidate_id = can.id;

-- Summary stats
SELECT 
  'Total committees' AS metric,
  COUNT(*) AS value
FROM nc_committee_file
UNION ALL
SELECT 
  'Matched committees',
  COUNT(*)
FROM committee_candidates
UNION ALL
SELECT 
  'Avg confidence score',
  ROUND(AVG(confidence)::numeric, 3)
FROM committee_candidates
UNION ALL
SELECT 
  'Donations with candidate_id',
  COUNT(*)
FROM nc_boe_donations_raw
WHERE candidate_id IS NOT NULL;
