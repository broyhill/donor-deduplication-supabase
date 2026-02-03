# Donor Deduplication and Identity Resolution System

This repository powers a scalable donor data cleaning and deduplication pipeline for political contributions, using Supabase and Python.

## Features

- **Name Matching**: Resolves thousands of name variants to a single identity using the `person_aliases` table.
- **Spouse Detection**: Automatically infers spousal relationships using address + last name.
- **Household Grouping**: Generates stable `household_id`s for grouping donors at the same address.
- **Pipeline Integration**: Python-based intake pipeline cleans, normalizes, and enriches any user-uploaded donor file.
- **Fuzzy Matching**: Handles unmatched names with configurable similarity thresholds.

## Project Structure

```
scripts/
  run_pipeline.py           # Master runner
  parse_names.py              # Name parser
  normalize_addresses.py      # Address parser
  assign_master_ids.py        # Alias matcher
  infer_spouses.py            # Spouse detection
  household_id_builder.py     # UUID generator
  fuzzy_match_unknowns.py     # Fuzzy matching for unresolved names
data/
  cleaned/person_aliases.csv  # Canonical name -> master ID mapping
sql/
  create_tables.sql           # DB schema setup
  load_person_aliases.sql     # Bulk import of aliases
  detect_spouses.sql          # Address-based spouse detection
  update_master_person_ids.sql# Generates master IDs
  views.sql                   # Common query views
requirements.txt              # Python dependencies
.env.example                  # Environment template
```

## Data Model

### `nc_boe_donations_raw`
| Column             | Purpose                                     |
|--------------------|---------------------------------------------|
| donor_name         | Raw input name                              |
| normalized_name    | Cleaned and standardized                    |
| master_person_id   | Linked identity via aliases                 |
| address            | Raw address field                           |
| house_number       | Parsed house number                         |
| street_name        | Parsed street name                          |
| zip_code           | Used in clustering                          |
| household_id       | UUID assigned per unique address cluster    |

### `person_aliases`
Stores canonical aliases and match confidence per identity.

### `donor_spouses`
Stores inferred spouse pairs based on household and name similarity.

## Setup Instructions

1. Clone the repo
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```
3. Copy environment template:
```bash
cp .env.example .env
```
4. Edit `.env` with your Supabase credentials
5. Run the pipeline:
```bash
python scripts/run_pipeline.py --full
```

## Outputs

- `cleaned_donor_file_enriched.csv`
- `inferred_spouses.csv`
- `household_summary.csv`

## SQL Views

The `sql/views.sql` file includes common query views:
- `v_total_by_person` - Total donations per person
- `v_total_by_household` - Total donations per household
- `v_unmatched_donors` - Donors without master_person_id
- `v_donor_spouses` - Donor-to-spouse links

## Next Steps

This system is designed to support:
- Fuzzy name resolution for unmatched entries
- Real-time feedback in your upload UI
- Voter file syncing (Data Trust, etc.)

## License

MIT License
