#!/usr/bin/env python3
"""
assign_master_ids.py

Master ID assignment for donor deduplication.
Creates blocking keys and assigns master_person_id using fuzzy matching.
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from parse_names import parse_name
from normalize_addresses import normalize_address, normalize_zip

@dataclass
class DonorRecord:
    """Represents a donor record for deduplication."""
    id: int
    prefix: str
    first_name: str
    middle_name: str
    last_name: str
    suffix: str
    street_address: str
    city: str
    state: str
    zipcode: str
    master_person_id: Optional[str] = None

def create_blocking_key(last_name: str, zipcode: str, first_initial: str) -> str:
    """Create blocking key for candidate grouping."""
    ln = (last_name or '').upper().strip()[:5]
    z = normalize_zip(zipcode)[:3] if zipcode else ''
    fi = (first_initial or '').upper()[:1]
    return f"{ln}|{z}|{fi}"

def generate_master_id(components: Dict[str, str]) -> str:
    """Generate deterministic master_person_id from normalized components."""
    key_parts = [
        components.get('last_name', '').upper().strip(),
        components.get('first_name', '').upper().strip()[:3],
        components.get('zip', '')[:5],
        components.get('street_num', ''),
    ]
    key_string = '|'.join(key_parts)
    hash_obj = hashlib.sha256(key_string.encode())
    return f"MP_{hash_obj.hexdigest()[:12].upper()}"

def extract_street_number(address: str) -> str:
    """Extract street number from address."""
    if not address:
        return ''
    match = re.match(r'^(\d+)', address.strip())
    return match.group(1) if match else ''

def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate Jaro-Winkler similarity between two names."""
    if not name1 or not name2:
        return 0.0
    s1, s2 = name1.upper().strip(), name2.upper().strip()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    match_distance = max(0, max(len1, len2) // 2 - 1)
    s1_matches, s2_matches = [False] * len1, [False] * len2
    matches = transpositions = 0
    for i in range(len1):
        for j in range(max(0, i - match_distance), min(i + match_distance + 1, len2)):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    jaro = (matches/len1 + matches/len2 + (matches - transpositions/2)/matches) / 3
    prefix_len = sum(1 for i in range(min(4, len1, len2)) if s1[i] == s2[i])
    return jaro + prefix_len * 0.1 * (1 - jaro)

def match_records(r1: DonorRecord, r2: DonorRecord) -> Tuple[bool, float]:
    """Determine if two records match."""
    if r1.last_name.upper() != r2.last_name.upper():
        return False, 0.0
    fn_sim = calculate_name_similarity(r1.first_name, r2.first_name)
    zip_match = normalize_zip(r1.zipcode) == normalize_zip(r2.zipcode)
    sn1, sn2 = extract_street_number(r1.street_address), extract_street_number(r2.street_address)
    street_match = sn1 == sn2 and sn1 != ''
    score = (0.4 if fn_sim >= 0.9 else 0.3 if fn_sim >= 0.8 else 0)
    score += 0.3 if zip_match else 0
    score += 0.3 if street_match else 0
    return score >= 0.6, score

def assign_master_ids(records: List[DonorRecord]) -> List[DonorRecord]:
    """Assign master_person_id to donor records."""
    blocks = defaultdict(list)
    for r in records:
        key = create_blocking_key(r.last_name, r.zipcode, r.first_name[:1] if r.first_name else '')
        blocks[key].append(r)
    for block in blocks.values():
        assigned = set()
        for i, r in enumerate(block):
            if r.id in assigned:
                continue
            components = {'last_name': r.last_name, 'first_name': r.first_name,
                         'zip': r.zipcode, 'street_num': extract_street_number(r.street_address)}
            r.master_person_id = generate_master_id(components)
            assigned.add(r.id)
            for other in block[i+1:]:
                if other.id not in assigned and match_records(r, other)[0]:
                    other.master_person_id = r.master_person_id
                    assigned.add(other.id)
    return records

if __name__ == '__main__':
    test_records = [
        DonorRecord(1, '', 'JOHN', 'A', 'SMITH', '', '123 Main St', 'Raleigh', 'NC', '27601'),
        DonorRecord(2, 'MR', 'JOHN', 'ADAM', 'SMITH', '', '123 Main Street', 'Raleigh', 'NC', '27601'),
        DonorRecord(3, 'DR', 'JANE', 'B', 'SMITH', '', '456 Oak Ave', 'Raleigh', 'NC', '27601'),
        DonorRecord(4, '', 'ROBERT', '', 'JONES', 'JR', '789 Pine Rd', 'Charlotte', 'NC', '28202'),
        DonorRecord(5, '', 'BOB', '', 'JONES', 'JR', '789 Pine Road', 'Charlotte', 'NC', '28202'),
    ]
    print('Master ID Assignment Demo')
    print('=' * 60)
    for r in assign_master_ids(test_records):
        print(f"ID {r.id}: {r.first_name} {r.last_name} -> {r.master_person_id}")
