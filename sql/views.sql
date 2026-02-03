-- Donor Deduplication SQL Views
-- Common query views for analytics and reporting

-- View: Total donations per person
CREATE OR REPLACE VIEW v_total_by_person AS
SELECT
  master_person_id,
  COUNT(*) AS donation_count,
  SUM(amount) AS total_contributed
FROM nc_boe_donations_raw
WHERE master_person_id IS NOT NULL
GROUP BY master_person_id;

-- View: Total donations per household
CREATE OR REPLACE VIEW v_total_by_household AS
SELECT
  household_id,
  COUNT(*) AS donation_count,
  SUM(amount) AS total_contributed
FROM nc_boe_donations_raw
WHERE household_id IS NOT NULL
GROUP BY household_id;

-- View: Unmatched names (donors without master_person_id)
CREATE OR REPLACE VIEW v_unmatched_donors AS
SELECT *
FROM nc_boe_donations_raw
WHERE master_person_id IS NULL;

-- View: Donor-to-spouse links
CREATE OR REPLACE VIEW v_donor_spouses AS
SELECT
  d1.donor_name AS donor,
  d2.donor_name AS spouse,
  ds.household_key,
  ds.confidence
FROM donor_spouses ds
JOIN nc_boe_donations_raw d1 ON ds.donor_id = d1.id
JOIN nc_boe_donations_raw d2 ON ds.spouse_id = d2.id;

-- View: Top donors by total amount
CREATE OR REPLACE VIEW v_top_donors AS
SELECT
  master_person_id,
  MAX(donor_name) AS primary_name,
  COUNT(*) AS donation_count,
  SUM(amount) AS total_contributed,
  MIN(contribution_date) AS first_donation,
  MAX(contribution_date) AS last_donation
FROM nc_boe_donations_raw
WHERE master_person_id IS NOT NULL
GROUP BY master_person_id
ORDER BY total_contributed DESC;

-- View: Household summary with spouse pairs
CREATE OR REPLACE VIEW v_household_summary AS
SELECT
  h.household_id,
  h.address_key,
  COUNT(DISTINCT d.master_person_id) AS member_count,
  SUM(d.amount) AS household_total,
  STRING_AGG(DISTINCT d.donor_name, ', ') AS members
FROM households h
JOIN nc_boe_donations_raw d ON h.household_id = d.household_id
GROUP BY h.household_id, h.address_key;
