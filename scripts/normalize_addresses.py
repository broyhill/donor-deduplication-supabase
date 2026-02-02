#!/usr/bin/env python3
"""
normalize_addresses.py

Address normalization utilities for donor deduplication.
Standardizes street addresses, cities, states, and ZIP codes.
"""

import re
from typing import Dict, Optional

# Standard abbreviations for street types
STREET_ABBREVS = {
    'STREET': 'ST',
    'AVENUE': 'AVE',
    'BOULEVARD': 'BLVD',
    'DRIVE': 'DR',
    'LANE': 'LN',
    'ROAD': 'RD',
    'COURT': 'CT',
    'CIRCLE': 'CIR',
    'PLACE': 'PL',
    'TERRACE': 'TER',
    'TRAIL': 'TRL',
    'HIGHWAY': 'HWY',
    'PARKWAY': 'PKWY',
    'WAY': 'WAY',
    'NORTH': 'N',
    'SOUTH': 'S',
    'EAST': 'E',
    'WEST': 'W',
    'NORTHEAST': 'NE',
    'NORTHWEST': 'NW',
    'SOUTHEAST': 'SE',
    'SOUTHWEST': 'SW',
    'APARTMENT': 'APT',
    'SUITE': 'STE',
    'BUILDING': 'BLDG',
    'FLOOR': 'FL',
    'UNIT': 'UNIT',
    'PO BOX': 'PO BOX',
    'POST OFFICE BOX': 'PO BOX',
}

# State abbreviations
STATE_ABBREVS = {
    'NORTH CAROLINA': 'NC',
    'SOUTH CAROLINA': 'SC',
    'VIRGINIA': 'VA',
    'WEST VIRGINIA': 'WV',
    'GEORGIA': 'GA',
    'TENNESSEE': 'TN',
    'FLORIDA': 'FL',
    'ALABAMA': 'AL',
    'KENTUCKY': 'KY',
    'MARYLAND': 'MD',
    'DISTRICT OF COLUMBIA': 'DC',
    'NEW YORK': 'NY',
    'NEW JERSEY': 'NJ',
    'PENNSYLVANIA': 'PA',
    'TEXAS': 'TX',
    'CALIFORNIA': 'CA',
}

def normalize_address(address: str) -> str:
    """Normalize a street address to standard format."""
    if not address:
        return ''
    
    # Uppercase and strip whitespace
    addr = address.upper().strip()
    
    # Remove extra whitespace
    addr = re.sub(r'\s+', ' ', addr)
    
    # Remove punctuation except hyphens in unit numbers
    addr = re.sub(r'[.,#]', '', addr)
    
    # Standardize abbreviations
    for full, abbrev in STREET_ABBREVS.items():
        # Match whole words only
        pattern = r'\b' + full + r'\b'
        addr = re.sub(pattern, abbrev, addr)
    
    return addr

def normalize_city(city: str) -> str:
    """Normalize city name."""
    if not city:
        return ''
    
    # Uppercase and strip
    city = city.upper().strip()
    
    # Remove extra whitespace
    city = re.sub(r'\s+', ' ', city)
    
    # Common city name standardizations
    city = city.replace('SAINT ', 'ST ')
    city = city.replace('MOUNT ', 'MT ')
    city = city.replace('FORT ', 'FT ')
    
    return city

def normalize_state(state: str) -> str:
    """Normalize state to two-letter abbreviation."""
    if not state:
        return ''
    
    state = state.upper().strip()
    
    # If already 2 letters, return as-is
    if len(state) == 2:
        return state
    
    # Look up full name
    return STATE_ABBREVS.get(state, state)

def normalize_zip(zipcode: str) -> str:
    """Normalize ZIP code to 5-digit format."""
    if not zipcode:
        return ''
    
    # Extract digits only
    digits = re.sub(r'\D', '', str(zipcode))
    
    # Return first 5 digits
    if len(digits) >= 5:
        return digits[:5]
    elif len(digits) > 0:
        return digits.zfill(5)
    
    return ''

def normalize_full_address(street: str, city: str, state: str, zipcode: str) -> Dict[str, str]:
    """Normalize all address components and return standardized dict."""
    return {
        'street_normalized': normalize_address(street),
        'city_normalized': normalize_city(city),
        'state_normalized': normalize_state(state),
        'zip_normalized': normalize_zip(zipcode),
    }

def create_address_key(street: str, city: str, state: str, zipcode: str) -> str:
    """Create a normalized address key for matching."""
    norm = normalize_full_address(street, city, state, zipcode)
    return f"{norm['street_normalized']}|{norm['city_normalized']}|{norm['state_normalized']}|{norm['zip_normalized']}"


# Example usage and testing
if __name__ == '__main__':
    test_addresses = [
        ('123 Main Street', 'Raleigh', 'North Carolina', '27601'),
        ('456 Oak Avenue, Apt 2B', 'Charlotte', 'NC', '28202-1234'),
        ('789 PINE BLVD', 'WINSTON SALEM', 'nc', '27101'),
        ('P.O. Box 1234', 'Durham', 'NC', '27701'),
        ('1000 West Trade Street Suite 100', 'Charlotte', 'NORTH CAROLINA', '28202'),
    ]
    
    print('Address Normalization Results:')
    print('=' * 70)
    
    for street, city, state, zipcode in test_addresses:
        print(f'\nInput:')
        print(f'  Street: {street}')
        print(f'  City:   {city}')
        print(f'  State:  {state}')
        print(f'  ZIP:    {zipcode}')
        
        normalized = normalize_full_address(street, city, state, zipcode)
        print(f'Normalized:')
        print(f'  Street: {normalized["street_normalized"]}')
        print(f'  City:   {normalized["city_normalized"]}')
        print(f'  State:  {normalized["state_normalized"]}')
        print(f'  ZIP:    {normalized["zip_normalized"]}')
        
        key = create_address_key(street, city, state, zipcode)
        print(f'Address Key: {key}')
