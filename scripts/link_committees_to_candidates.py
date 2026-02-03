#!/usr/bin/env python3
"""
Committee to Candidate Linking Pipeline

Links political committees to candidates using county + fuzzy name matching.
Enriches donation records with candidate_id for direct candidate analysis.

Usage:
    python link_committees_to_candidates.py
    python link_committees_to_candidates.py --threshold 0.85 --export
"""

import os
import pandas as pd
from fuzzywuzzy import fuzz
from tqdm import tqdm
import click
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def get_supabase_client():
    """Initialize Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    return create_client(url, key)

def fuzzy_match_committee_to_candidate(committee_name: str, candidate_name: str) -> float:
    """
    Calculate similarity between committee name and candidate name.
    Uses token_sort_ratio for flexibility with name ordering.
    
    Returns:
        Similarity score between 0 and 1
    """
    if not committee_name or not candidate_name:
        return 0.0
    
    score = fuzz.token_sort_ratio(
        committee_name.lower().strip(),
        candidate_name.lower().strip()
    )
    return score / 100.0

def link_committees_to_candidates(client, threshold: float = 0.85) -> pd.DataFrame:
    """
    Match committees to candidates using county + fuzzy name matching.
    
    Args:
        client: Supabase client
        threshold: Minimum similarity score (0-1)
    
    Returns:
        DataFrame of committee-candidate matches
    """
    print("Loading committee data...")
    comm_resp = client.table('nc_committee_file').select('*').execute()
    committees = pd.DataFrame(comm_resp.data)
    
    print("Loading candidate data...")
    cand_resp = client.table('ncsbe_candidates').select('*').execute()
    candidates = pd.DataFrame(cand_resp.data)
    
    print(f"Matching {len(committees)} committees to {len(candidates)} candidates...")
    
    matches = []
    
    for _, comm in tqdm(committees.iterrows(), total=len(committees)):
        comm_county = str(comm.get('county_name', '')).lower().strip()
        comm_name = comm.get('committee_name', '')
        
        if not comm_county or not comm_name:
            continue
        
        # Filter candidates by same county
        county_candidates = candidates[
            candidates['county_name'].str.lower().str.strip() == comm_county
        ]
        
        best_match = None
        best_score = 0
        
        for _, cand in county_candidates.iterrows():
            cand_name = cand.get('name_on_ballot', '')
            score = fuzzy_match_committee_to_candidate(comm_name, cand_name)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = cand
        
        if best_match is not None:
            matches.append({
                'committee_id': comm.get('committee_id'),
                'committee_name': comm_name,
                'candidate_id': best_match.get('id'),
                'candidate_name': best_match.get('name_on_ballot'),
                'party': best_match.get('party'),
                'contest_name': best_match.get('contest_name'),
                'county_name': comm_county,
                'confidence': best_score,
                'match_type': 'county+fuzzy_name'
            })
    
    return pd.DataFrame(matches)

def save_matches_to_supabase(client, matches_df: pd.DataFrame):
    """Save matches to committee_candidates table."""
    if matches_df.empty:
        print("No matches to save.")
        return
    
    records = matches_df[[
        'committee_id', 'committee_name', 'candidate_id',
        'match_type', 'confidence', 'county_name'
    ]].to_dict('records')
    
    print(f"Saving {len(records)} matches...")
    client.table('committee_candidates').upsert(
        records, on_conflict='committee_id'
    ).execute()

def enrich_donations(client):
    """Update donation records with candidate_id from matched committees."""
    print("Enriching donation records with candidate_id...")
    
    # Get matches
    resp = client.table('committee_candidates').select('committee_id, candidate_id').execute()
    matches = {m['committee_id']: m['candidate_id'] for m in resp.data}
    
    # Get donations without candidate_id
    donations_resp = client.table('nc_boe_donations_raw').select('id, committee_id').is_('candidate_id', 'null').execute()
    
    updated = 0
    for donation in tqdm(donations_resp.data):
        comm_id = donation.get('committee_id')
        if comm_id in matches:
            client.table('nc_boe_donations_raw').update({
                'candidate_id': matches[comm_id]
            }).eq('id', donation['id']).execute()
            updated += 1
    
    print(f"Updated {updated} donation records with candidate_id")

@click.command()
@click.option('--threshold', default=0.85, help='Minimum similarity score (0-1)')
@click.option('--export', is_flag=True, help='Export matches to CSV for review')
@click.option('--enrich', is_flag=True, help='Update donations with candidate_id')
def main(threshold, export, enrich):
    """Link committees to candidates and enrich donation records."""
    client = get_supabase_client()
    
    # Match committees to candidates
    matches_df = link_committees_to_candidates(client, threshold=threshold)
    
    print(f"\nFound {len(matches_df)} committee-candidate matches")
    
    if not matches_df.empty:
        print(f"Average confidence: {matches_df['confidence'].mean():.3f}")
        print(f"Min confidence: {matches_df['confidence'].min():.3f}")
        print(f"Max confidence: {matches_df['confidence'].max():.3f}")
        
        if export:
            output_file = 'data/cleaned/committee_candidate_matches.csv'
            matches_df.to_csv(output_file, index=False)
            print(f"Exported matches to {output_file}")
        
        # Save to database
        save_matches_to_supabase(client, matches_df)
        
        if enrich:
            enrich_donations(client)
    
    print("\nDone!")

if __name__ == '__main__':
    main()
