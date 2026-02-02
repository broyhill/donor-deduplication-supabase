-- ============================================
-- Schema Validation Queries
-- Verify data integrity and schema compliance
-- ============================================

-- ============================================
-- 1. Check required columns exist in donations_normalized
-- ============================================
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'donations_normalized'
  AND table_schema = 'public'
ORDER BY ordinal_position;

-- ============================================
-- 2. Validate all donations have required fields
-- ============================================
SELECT 
    'Missing last_name' as issue,
    COUNT(*) as count
FROM donations_normalized
WHERE last_name IS NULL OR TRIM(last_name) = ''
UNION ALL
SELECT 
    'Missing first_name',
    COUNT(*)
FROM donations_normalized
WHERE first_name IS NULL OR TRIM(first_name) = ''
UNION ALL
SELECT 
    'Missing master_person_id',
    COUNT(*)
FROM donations_normalized
WHERE master_person_id IS NULL;

-- ============================================
-- 3. Check for orphaned aliases
-- ============================================
SELECT COUNT(*) as orphaned_aliases
FROM person_aliases pa
LEFT JOIN person_master pm ON pa.master_person_id = pm.master_person_id
WHERE pm.master_person_id IS NULL;

-- ============================================
-- 4. Validate address normalization
-- ============================================
SELECT 
    'Has house_number' as field,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM donations_normalized), 0), 2) as pct
FROM donations_normalized
WHERE house_number IS NOT NULL AND TRIM(house_number) != ''
UNION ALL
SELECT 
    'Has street_name',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM donations_normalized), 0), 2)
FROM donations_normalized
WHERE street_name IS NOT NULL AND TRIM(street_name) != ''
UNION ALL
SELECT 
    'Has city',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM donations_normalized), 0), 2)
FROM donations_normalized
WHERE city IS NOT NULL AND TRIM(city) != ''
UNION ALL
SELECT 
    'Has zip_code',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM donations_normalized), 0), 2)
FROM donations_normalized
WHERE zip_code IS NOT NULL AND TRIM(zip_code) != '';

-- ============================================
-- 5. Schema compliance summary
-- ============================================
SELECT 
    'person_master' as table_name,
    COUNT(*) as row_count
FROM person_master
UNION ALL
SELECT 'person_aliases', COUNT(*) FROM person_aliases
UNION ALL
SELECT 'person_addresses', COUNT(*) FROM person_addresses
UNION ALL
SELECT 'donations_normalized', COUNT(*) FROM donations_normalized
UNION ALL
SELECT 'nc_boe_donations_raw', COUNT(*) FROM nc_boe_donations_raw;
