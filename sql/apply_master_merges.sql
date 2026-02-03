-- Apply master_person_id merges to unify fragmented identities
-- This script merges duplicate master_person_ids into a single canonical identity

-- Create merge tracking table if not exists
CREATE TABLE IF NOT EXISTS master_person_merges (
  id SERIAL PRIMARY KEY,
  old_id UUID NOT NULL,
  new_id UUID NOT NULL,
  merged_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(old_id)
);

-- Import merge plan from CSV (run from Python or use COPY command)
-- COPY master_person_merges(old_id, new_id) FROM '/path/to/master_person_merges.csv' CSV HEADER;

-- Apply the merges to nc_boe_donations_raw
UPDATE nc_boe_donations_raw d
SET master_person_id = m.new_id
FROM master_person_merges m
WHERE d.master_person_id = m.old_id;

-- Verify merge results
SELECT 
  'total_merges' as metric, 
  COUNT(*)::text as value 
FROM master_person_merges
UNION ALL
SELECT 
  'records_updated',
  COUNT(*)::text
FROM nc_boe_donations_raw d
JOIN master_person_merges m ON d.master_person_id = m.new_id;
