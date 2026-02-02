#!/usr/bin/env python3
"""
Name Parsing Module for Donor Deduplication

Parses donor names into standardized 6-part format:
- prefix (Mr., Mrs., Dr., Rev., Hon., etc.)
- first_name
- middle_name
- last_name  
- suffix (Jr., Sr., III, IV, PhD, etc.)
- nickname (optional)
"""

import re
from typing import Dict, Optional

# Common name prefixes
PREFIXES = {
    'MR', 'MRS', 'MS', 'MISS', 'DR', 'REV', 'HON', 
    'JUDGE', 'SEN', 'REP', 'GOV', 'MAYOR', 'PROF',
    'FR', 'SR', 'BROTHER', 'SISTER', 'PASTOR'
}

# Common name suffixes
SUFFIXES = {
    'JR', 'SR', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII',
    'MD', 'PHD', 'ESQ', 'CPA', 'DDS', 'RN', 'JD', 'DO',
    'MBA', 'MPA', 'PE', 'RA', 'AIA', 'FAIA'
}


def parse_name(full_name: str) -> Dict[str, Optional[str]]:
    """
    Parse a full name string into component parts.
    
    Args:
        full_name: Raw name string (e.g., "DR. FRED G. HUEBNER III")
        
    Returns:
        Dictionary with keys: prefix, first_name, middle_name, last_name, suffix, nickname
    """
    result = {
        'prefix': None,
        'first_name': None,
        'middle_name': None,
        'last_name': None,
        'suffix': None,
        'nickname': None
    }
    
    if not full_name or not full_name.strip():
        return result
    
    # Normalize: uppercase, remove extra spaces
    name = full_name.upper().strip()
    
    # Extract nickname in quotes or parentheses
    nickname_match = re.search(r'["\(]([^"\)]+)["\)]', name)
    if nickname_match:
        result['nickname'] = nickname_match.group(1).title()
        name = re.sub(r'["\(][^"\)]+["\)]', '', name)
    
    # Remove periods and normalize spaces
    name = re.sub(r'\.', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Split into parts
    parts = name.split()
    
    if not parts:
        return result
    
    # Extract prefix if present
    if parts[0] in PREFIXES:
        result['prefix'] = parts.pop(0).title()
        if result['prefix'] == 'Dr':
            result['prefix'] = 'Dr.'
        elif result['prefix'] == 'Mr':
            result['prefix'] = 'Mr.'
        elif result['prefix'] == 'Mrs':
            result['prefix'] = 'Mrs.'
        elif result['prefix'] == 'Ms':
            result['prefix'] = 'Ms.'
        elif result['prefix'] == 'Rev':
            result['prefix'] = 'Rev.'
    
    if not parts:
        return result
    
    # Extract suffix if present (check last part)
    if parts[-1] in SUFFIXES:
        result['suffix'] = parts.pop()
    
    if not parts:
        return result
    
    # Now assign remaining parts
    if len(parts) == 1:
        # Only one part - assume it's last name
        result['last_name'] = parts[0].title()
    elif len(parts) == 2:
        # Two parts - first and last
        result['first_name'] = parts[0].title()
        result['last_name'] = parts[1].title()
    else:
        # Three or more parts - first, middle(s), last
        result['first_name'] = parts[0].title()
        result['last_name'] = parts[-1].title()
        # Join middle names if multiple
        result['middle_name'] = ' '.join(p.title() for p in parts[1:-1])
    
    return result


def parse_names_batch(names: list) -> list:
    """Parse a batch of names."""
    return [parse_name(name) for name in names]


# Example usage and testing
if __name__ == '__main__':
    test_names = [
        'JUSTIN HUDSON',
        'L MORRIS HUDSON',
        'FRED G. HUEBNER III',
        'CAROL HUFF',
        'J. HUFF',
        'LINDA HUFF',
        'DR. JAMES ARTHUR POPE JR',
        'MRS. MARY ANN SMITH-JONES',
        'REV. BILLY GRAHAM',
        'HON. ART POPE',
        'ROBERT "BOB" SMITH'
    ]
    
    print('Name Parsing Results (6-part format):')
    print('=' * 70)
    
    for name in test_names:
        parsed = parse_name(name)
        print(f'\nInput: {name}')
        print(f'  Prefix:   {parsed["prefix"]}')
        print(f'  First:    {parsed["first_name"]}')
        print(f'  Middle:   {parsed["middle_name"]}')
        print(f'  Last:     {parsed["last_name"]}')
        print(f'  Suffix:   {parsed["suffix"]}')
        print(f'  Nickname: {parsed["nickname"]}')
