# Schema Reference

This document describes the database schema for donor deduplication in Supabase.

## Tables Overview

### 1. nc_boe_donations_raw
Raw donation records from NC Board of Elections.

| Column | Type | Description |
|--------|------|-------------|
| id | bigint | Primary key, auto-increment |
| account_id | text | BOE account identifier |
| committee_name | text | Political committee name |
| contributor_name | text | Full name as reported |
| street_1 | text | Address line 1 |
| street_2 | text | Address line 2 |
| city | text | City |
| state | text | State abbreviation |
| zip | text | ZIP code |
| profession | text | Contributor profession |
| employer | text | Contributor employer |
| date | date | Contribution date |
| amount | decimal | Contribution amount |
| form_of_payment | text | Payment method |
| purpose | text | Contribution purpose |
| declaration | text | Declaration text |

### 2. donor_master
Deduplicated master donor records.

| Column | Type | Description |
|--------|------|-------------|
| master_person_id | text | Primary key (MP_xxxx format) |
| prefix | text | Name prefix (Dr., Mr., etc.) |
| first_name | text | Normalized first name |
| middle_name | text | Middle name/initial |
| last_name | text | Normalized last name |
| suffix | text | Name suffix (Jr., III, etc.) |
| street_normalized | text | Standardized street address |
| city_normalized | text | Standardized city |
| state_normalized | text | 2-letter state code |
| zip_normalized | text | 5-digit ZIP |
| created_at | timestamp | Record creation time |
| updated_at | timestamp | Last update time |

### 3. donation_to_master_mapping
Links raw donations to master records.

| Column | Type | Description |
|--------|------|-------------|
| id | bigint | Primary key |
| raw_donation_id | bigint | FK to nc_boe_donations_raw |
| master_person_id | text | FK to donor_master |
| confidence_score | decimal | Match confidence (0-1) |
| match_method | text | How match was determined |
| created_at | timestamp | Mapping creation time |

## Indexes

```sql
-- Blocking key index for efficient matching
CREATE INDEX idx_donor_blocking ON donor_master(
  LEFT(last_name, 5),
  LEFT(zip_normalized, 3),
  LEFT(first_name, 1)
);

-- Raw donations lookup
CREATE INDEX idx_raw_contributor ON nc_boe_donations_raw(contributor_name);
CREATE INDEX idx_raw_date ON nc_boe_donations_raw(date);
```

## Master ID Generation

Master person IDs follow format: `MP_` + 12-char SHA256 hash

Components used for hash:
1. Normalized last name (uppercase)
2. First 3 chars of first name (uppercase)
3. 5-digit ZIP code
4. Street number only

## Name Parsing (6-part format)

Names are parsed into 6 components:
- **Prefix**: Dr., Mr., Mrs., Rev., Hon., etc.
- **First Name**: Given name
- **Middle Name**: Middle name or initial
- **Last Name**: Family/surname
- **Suffix**: Jr., Sr., III, MD, PhD, etc.
- **Full Name**: Original unparsed name (preserved)

## Address Normalization

Addresses are standardized using:
- Street type abbreviations (STREET -> ST, AVENUE -> AVE)
- Directional abbreviations (NORTH -> N, SOUTHWEST -> SW)
- Unit indicators (APARTMENT -> APT, SUITE -> STE)
- State full names to 2-letter codes
- ZIP codes truncated to 5 digits
