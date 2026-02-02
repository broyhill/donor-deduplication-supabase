# donor-deduplication-supabase

Donor deduplication and standardization for political contributions using Supabase, SQL, and fuzzy name matching.

## Overview

This project provides tools for deduplicating donor records from NC Board of Elections campaign finance data. It assigns unique `master_person_id` values to link multiple donation records to the same individual donor.

## Features

- **6-part name parsing**: Parses names into prefix, first, middle, last, suffix, and full name
- **Address normalization**: Standardizes street addresses, cities, states, and ZIP codes
- **Blocking-based matching**: Efficient deduplication using blocking keys
- **Deterministic master IDs**: Consistent ID generation using SHA-256 hashing
- **Fuzzy matching**: Jaro-Winkler similarity for name matching

## Project Structure

```
donor-deduplication-supabase/
├── data/
│   ├── raw/           # Raw input data files
│   └── cleaned/       # Processed output files
├── docs/
│   └── schema_reference.md  # Database schema documentation
├── scripts/
│   ├── parse_names.py           # Name parsing utilities
│   ├── normalize_addresses.py   # Address standardization
│   └── assign_master_ids.py     # Master ID assignment
├── sql/
│   ├── create_tables.sql        # Table creation DDL
│   ├── update_master_person_ids.sql  # ID update queries
│   └── validate_schema.sql      # Schema validation
├── .gitignore
└── README.md
```

## Usage

### Name Parsing

```python
from scripts.parse_names import parse_name

result = parse_name('DR. JAMES ARTHUR POPE JR')
# Returns: {
#   'prefix': 'DR',
#   'first_name': 'JAMES',
#   'middle_name': 'ARTHUR',
#   'last_name': 'POPE',
#   'suffix': 'JR',
#   'full_name': 'DR. JAMES ARTHUR POPE JR'
# }
```

### Address Normalization

```python
from scripts.normalize_addresses import normalize_full_address

result = normalize_full_address(
    '123 Main Street',
    'Raleigh',
    'North Carolina',
    '27601-1234'
)
# Returns: {
#   'street_normalized': '123 MAIN ST',
#   'city_normalized': 'RALEIGH',
#   'state_normalized': 'NC',
#   'zip_normalized': '27601'
# }
```

## Database Schema

See [docs/schema_reference.md](docs/schema_reference.md) for complete schema documentation.

### Key Tables

- `nc_boe_donations_raw`: Raw donation records from NC BOE
- `donor_master`: Deduplicated master donor records
- `donation_to_master_mapping`: Links donations to master records

## Requirements

- Python 3.8+
- Supabase account
- PostgreSQL (via Supabase)

## License

Private repository - All rights reserved.
