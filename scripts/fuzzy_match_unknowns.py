#!/usr/bin/env python3
"""
Fuzzy Matching for Unmatched Donor Names

Finds potential matches for donors that couldn't be matched via exact alias lookup.
Outputs suggestions for manual review before adding to person_aliases.

Usage:
    python fuzzy_match_unknowns.py --threshold 88 --output fuzzy_matches_review.csv
"""

import pandas as pd
from fuzzywuzzy import process, fuzz
from tqdm import tqdm
import click

def fuzzy_match_unmatched(df: pd.DataFrame, alias_df: pd.DataFrame, 
                          threshold: int = 88, name_col: str = 'normalized_name') -> pd.DataFrame:
    """
    Find fuzzy matches for donors without master_person_id.
    
    Args:
        df: Main donor DataFrame with normalized_name column
        alias_df: DataFrame of known aliases with alias_name and master_person_id
        threshold: Minimum similarity score (0-100) to consider a match
        name_col: Column name containing normalized names
    
    Returns:
        DataFrame of suggested matches for review
    """
    # Filter to unmatched records
    unmatched = df[df['master_person_id'].isnull()].copy()
    
    if unmatched.empty:
        print("No unmatched records found!")
        return pd.DataFrame()
    
    print(f"Processing {len(unmatched)} unmatched records...")
    
    # Build list of known aliases for matching
    known_aliases = alias_df['alias_name'].tolist()
    
    matched_rows = []
    
    for idx, row in tqdm(unmatched.iterrows(), total=len(unmatched)):
        name = row.get(name_col) or row.get('donor_name', '')
        
        if not name or pd.isna(name):
            continue
        
        # Find best match using token_sort_ratio for name flexibility
        result = process.extractOne(
            name, 
            known_aliases,
            scorer=fuzz.token_sort_ratio
        )
        
        if result:
            match, score, _ = result
            
            if score >= threshold:
                match_row = alias_df[alias_df['alias_name'] == match].iloc[0]
                matched_rows.append({
                    'original_id': row.get('id'),
                    'original_name': row.get('donor_name'),
                    'normalized_name': name,
                    'suggested_alias': match,
                    'similarity_score': score,
                    'suggested_master_person_id': match_row['master_person_id'],
                    'canonical_name': match_row.get('canonical_name', ''),
                    'review_status': 'pending'
                })
    
    result_df = pd.DataFrame(matched_rows)
    
    # Sort by similarity score descending
    if not result_df.empty:
        result_df = result_df.sort_values('similarity_score', ascending=False)
    
    return result_df


def add_approved_matches_to_aliases(review_df: pd.DataFrame, 
                                     alias_df: pd.DataFrame) -> pd.DataFrame:
    """
    After manual review, add approved matches to the alias table.
    
    Args:
        review_df: Reviewed DataFrame with 'review_status' column
        alias_df: Existing alias DataFrame
    
    Returns:
        Updated alias DataFrame with new entries
    """
    approved = review_df[review_df['review_status'] == 'approved']
    
    new_aliases = []
    for _, row in approved.iterrows():
        new_aliases.append({
            'alias_name': row['original_name'],
            'canonical_name': row['canonical_name'],
            'master_person_id': row['suggested_master_person_id'],
            'match_type': 'fuzzy',
            'confidence': row['similarity_score'] / 100.0
        })
    
    if new_aliases:
        new_df = pd.DataFrame(new_aliases)
        return pd.concat([alias_df, new_df], ignore_index=True)
    
    return alias_df


@click.command()
@click.option('--threshold', default=88, help='Minimum similarity score (0-100)')
@click.option('--output', default='data/cleaned/fuzzy_matches_review.csv', 
              help='Output file for review')
@click.option('--donors', default='donor_master', help='Source table name')
@click.option('--aliases', default='person_aliases', help='Alias table name')
def main(threshold, output, donors, aliases):
    """Find fuzzy matches for unmatched donor names."""
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    client = create_client(url, key)
    
    # Load data
    print("Loading donor data...")
    donor_resp = client.table(donors).select('*').is_('master_person_id', 'null').execute()
    df = pd.DataFrame(donor_resp.data)
    
    print("Loading alias data...")
    alias_resp = client.table(aliases).select('*').execute()
    alias_df = pd.DataFrame(alias_resp.data)
    
    # Find matches
    suggestions = fuzzy_match_unmatched(df, alias_df, threshold=threshold)
    
    if not suggestions.empty:
        suggestions.to_csv(output, index=False)
        print(f"\nFound {len(suggestions)} potential matches")
        print(f"Results saved to: {output}")
        print("\nReview the file, update 'review_status' to 'approved' for valid matches,")
        print("then use add_approved_matches_to_aliases() to update your alias table.")
    else:
        print("No fuzzy matches found above threshold.")


if __name__ == '__main__':
    main()
