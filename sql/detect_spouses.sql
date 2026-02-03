-- ================================================================
-- DETECT AND INSERT SPOUSE RELATIONSHIPS
-- Pairs donors who share same address block + last name
-- ================================================================

-- Enable uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create donor_spouses table for tracking spouse relationships
CREATE TABLE IF NOT EXISTS donor_spouses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  donor_id BIGINT,
  spouse_id BIGINT,
  household_key TEXT,
  confidence NUMERIC(3,2),
  source TEXT DEFAULT 'address_inference',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(donor_id, spouse_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_donor_spouses_household ON donor_spouses(household_key);
CREATE INDEX IF NOT EXISTS idx_donor_spouses_donor ON donor_spouses(donor_id);
CREATE INDEX IF NOT EXISTS idx_donor_spouses_spouse ON donor_spouses(spouse_id);

-- Insert spouse pairs where donors share same address block + last name
-- This example is scoped to Broyhill donors; remove WHERE clause for all donors
INSERT INTO donor_spouses (donor_id, spouse_id, household_key, confidence, source)
SELECT DISTINCT ON (LEAST(a.id, b.id), GREATEST(a.id, b.id))
  a.id AS donor_id,
  b.id AS spouse_id,
  LOWER(CONCAT(
    COALESCE((regexp_match(a.street_line_1, '^(\d+)'))[1], ''),
    '_',
    a.zip_code
  )) AS household_key,
  0.95 AS confidence,
  'address_lastname_match' AS source
FROM nc_boe_donations_raw a
JOIN nc_boe_donations_raw b
  ON a.zip_code = b.zip_code
  AND a.street_line_1 IS NOT NULL
  AND b.street_line_1 IS NOT NULL
  AND (regexp_match(a.street_line_1, '^(\d+)'))[1] = (regexp_match(b.street_line_1, '^(\d+)'))[1]
  AND a.id < b.id
  AND UPPER((regexp_match(TRIM(a.donor_name), '(\S+)$'))[1]) = UPPER((regexp_match(TRIM(b.donor_name), '(\S+)$'))[1])
WHERE a.donor_name ILIKE '%Broyhill%'
  AND b.donor_name ILIKE '%Broyhill%'
ON CONFLICT (donor_id, spouse_id) DO NOTHING;
