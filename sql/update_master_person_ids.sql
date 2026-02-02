-- ============================================
-- Update Master Person IDs in Donations
-- Links raw donations to deduplicated person records
-- ============================================

-- ============================================
-- STEP 1: Create or find master person from parsed name
-- ============================================
CREATE OR REPLACE FUNCTION get_or_create_master_person(
    p_first_name VARCHAR,
    p_middle_name VARCHAR,
    p_last_name VARCHAR,
    p_suffix VARCHAR
) RETURNS UUID AS $$
DECLARE
    v_master_id UUID;
BEGIN
    -- Try to find existing master person (exact match)
    SELECT master_person_id INTO v_master_id
    FROM person_master
    WHERE UPPER(TRIM(canonical_first_name)) = UPPER(TRIM(p_first_name))
      AND UPPER(TRIM(canonical_last_name)) = UPPER(TRIM(p_last_name))
      AND (canonical_suffix IS NULL AND p_suffix IS NULL 
           OR UPPER(TRIM(canonical_suffix)) = UPPER(TRIM(p_suffix)))
    LIMIT 1;
    
    -- If not found, create new master person
    IF v_master_id IS NULL THEN
        INSERT INTO person_master (
            canonical_first_name,
            canonical_middle_name,
            canonical_last_name,
            canonical_suffix
        ) VALUES (
            INITCAP(TRIM(p_first_name)),
            INITCAP(TRIM(p_middle_name)),
            INITCAP(TRIM(p_last_name)),
            UPPER(TRIM(p_suffix))
        )
        RETURNING master_person_id INTO v_master_id;
    END IF;
    
    RETURN v_master_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 2: Assign master_person_id to normalized donations
-- ============================================
UPDATE donations_normalized dn
SET master_person_id = get_or_create_master_person(
    dn.first_name,
    dn.middle_name,
    dn.last_name,
    dn.suffix
)
WHERE dn.master_person_id IS NULL;

-- ============================================
-- STEP 3: Create alias records for tracking
-- ============================================
INSERT INTO person_aliases (
    master_person_id,
    alias_name,
    alias_first_name,
    alias_middle_name,
    alias_last_name,
    alias_suffix,
    source_table,
    source_id,
    match_type
)
SELECT DISTINCT
    dn.master_person_id,
    raw.donor_name,
    dn.first_name,
    dn.middle_name,
    dn.last_name,
    dn.suffix,
    'nc_boe_donations_raw',
    dn.raw_id,
    'exact'
FROM donations_normalized dn
JOIN nc_boe_donations_raw raw ON dn.raw_id = raw.id
WHERE dn.master_person_id IS NOT NULL
ON CONFLICT (alias_name, source_table, source_id) DO NOTHING;

-- ============================================
-- STEP 4: Summary of assignments
-- ============================================
SELECT 
    'Total donations' as metric,
    COUNT(*) as count
FROM donations_normalized
UNION ALL
SELECT 
    'With master_person_id',
    COUNT(*)
FROM donations_normalized
WHERE master_person_id IS NOT NULL
UNION ALL
SELECT 
    'Unique persons',
    COUNT(DISTINCT master_person_id)
FROM donations_normalized;
