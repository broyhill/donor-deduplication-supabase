"""Spouse Inference Module

Detects potential spouse pairs based on shared address and last name.
Part of the donor deduplication pipeline.
"""

import pandas as pd
from typing import Optional


def infer_spouse_pairs(df: pd.DataFrame, 
                       id_col: str = 'id',
                       house_number_col: str = 'house_number',
                       street_name_col: str = 'street_name', 
                       zip_col: str = 'zip_code',
                       last_name_col: str = 'last_name') -> pd.DataFrame:
    """
    Infer spouse pairs from donor data based on shared address and last name.
    
    Args:
        df: DataFrame with donor records
        id_col: Column name for unique ID
        house_number_col: Column for house number
        street_name_col: Column for street name  
        zip_col: Column for zip code
        last_name_col: Column for last name
        
    Returns:
        DataFrame with columns: donor_id, spouse_id, household_key, confidence, source
    """
    df = df.copy()
    
    # Create household key from address components
    df['household_key'] = (
        df[house_number_col].fillna('').astype(str) + '_' +
        df[street_name_col].fillna('') + '_' +
        df[zip_col].fillna('')
    ).str.lower()
    
    # Group by household key
    household_groups = df.groupby('household_key')
    
    spouse_rows = []
    
    for key, group in household_groups:
        if len(group) < 2:
            continue
            
        # Compare each pair within household
        for i, donor1 in group.iterrows():
            for j, donor2 in group.iterrows():
                if i >= j:
                    continue
                    
                # Check if last names match
                ln1 = str(donor1.get(last_name_col, '')).upper()
                ln2 = str(donor2.get(last_name_col, '')).upper()
                
                if ln1 and ln2 and ln1 == ln2:
                    spouse_rows.append({
                        'donor_id': donor1[id_col],
                        'spouse_id': donor2[id_col],
                        'household_key': key,
                        'confidence': 0.95,
                        'source': 'address_lastname_match'
                    })
    
    return pd.DataFrame(spouse_rows)


def add_spouse_columns(df: pd.DataFrame, 
                       spouse_df: pd.DataFrame,
                       id_col: str = 'id') -> pd.DataFrame:
    """
    Add spouse information back to main donor DataFrame.
    
    Args:
        df: Main donor DataFrame
        spouse_df: DataFrame of spouse pairs from infer_spouse_pairs()
        id_col: Column name for unique ID
        
    Returns:
        DataFrame with added spouse_id and has_spouse columns
    """
    df = df.copy()
    
    # Create lookup of donor_id -> spouse_id
    spouse_lookup = dict(zip(spouse_df['donor_id'], spouse_df['spouse_id']))
    reverse_lookup = dict(zip(spouse_df['spouse_id'], spouse_df['donor_id']))
    spouse_lookup.update(reverse_lookup)
    
    df['spouse_id'] = df[id_col].map(spouse_lookup)
    df['has_spouse'] = df['spouse_id'].notna()
    
    return df


if __name__ == '__main__':
    # Example usage
    print("Spouse inference module loaded.")
    print("Usage: from scripts.infer_spouses import infer_spouse_pairs")
