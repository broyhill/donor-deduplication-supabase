#!/usr/bin/env python3
"""
Household ID Builder

Assigns stable household_id UUIDs to group donors at the same address.
Uses normalized address components to create consistent household keys.

Usage:
    python household_id_builder.py
"""

import uuid
import hashlib
import pandas as pd
from typing import Optional

def create_address_key(row: pd.Series, 
                       street_col: str = 'street_line_1',
                       city_col: str = 'city',
                       zip_col: str = 'zip_code') -> Optional[str]:
    """
    Create a normalized address key for household grouping.
    
    Args:
        row: DataFrame row with address components
        street_col: Column name for street address
        city_col: Column name for city
        zip_col: Column name for ZIP code
    
    Returns:
        Normalized address key string or None if insufficient data
    """
    street = str(row.get(street_col, '')).upper().strip()
    city = str(row.get(city_col, '')).upper().strip()
    zip_code = str(row.get(zip_col, ''))[:5].strip()
    
    # Require at least street and zip
    if not street or not zip_code or street == 'NAN' or zip_code == 'NAN':
        return None
    
    # Normalize common abbreviations
    street = street.replace(' STREET', ' ST')
    street = street.replace(' AVENUE', ' AVE')
    street = street.replace(' DRIVE', ' DR')
    street = street.replace(' ROAD', ' RD')
    street = street.replace(' LANE', ' LN')
    street = street.replace(' COURT', ' CT')
    street = street.replace(' CIRCLE', ' CIR')
    street = street.replace(' BOULEVARD', ' BLVD')
    
    # Remove extra whitespace
    street = ' '.join(street.split())
    
    return f"{street}|{city}|{zip_code}"


def generate_household_id(address_key: str) -> str:
    """
    Generate a deterministic UUID from an address key.
    Same address always produces the same household_id.
    
    Args:
        address_key: Normalized address string
    
    Returns:
        UUID string
    """
    # Create deterministic UUID using SHA-256 hash
    hash_bytes = hashlib.sha256(address_key.encode()).digest()[:16]
    return str(uuid.UUID(bytes=hash_bytes))


def assign_household_ids(df: pd.DataFrame,
                         street_col: str = 'street_line_1',
                         city_col: str = 'city', 
                         zip_col: str = 'zip_code') -> pd.DataFrame:
    """
    Assign household_id to all rows based on address.
    
    Args:
        df: DataFrame with address columns
        street_col: Column name for street address
        city_col: Column name for city
        zip_col: Column name for ZIP code
    
    Returns:
        DataFrame with added household_id and address_key columns
    """
    df = df.copy()
    
    # Create address keys
    df['address_key'] = df.apply(
        lambda row: create_address_key(row, street_col, city_col, zip_col),
        axis=1
    )
    
    # Generate household IDs
    df['household_id'] = df['address_key'].apply(
        lambda key: generate_household_id(key) if key else None
    )
    
    return df


def build_households_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a households summary table.
    
    Args:
        df: DataFrame with household_id assigned
    
    Returns:
        DataFrame with unique households and member counts
    """
    households = df[df['household_id'].notna()].groupby('household_id').agg({
        'address_key': 'first',
        'id': 'count',
        'donor_name': lambda x: ', '.join(x.unique()[:5])  # First 5 members
    }).reset_index()
    
    households.columns = ['household_id', 'address_key', 'member_count', 'members_sample']
    
    return households


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    client = create_client(url, key)
    
    print("Loading donor data...")
    response = client.table('nc_boe_donations_raw').select('*').execute()
    df = pd.DataFrame(response.data)
    
    print(f"Processing {len(df)} records...")
    df = assign_household_ids(df)
    
    # Count households
    household_count = df['household_id'].nunique()
    print(f"Found {household_count} unique households")
    
    # Build households table
    households = build_households_table(df)
    
    print(f"\nHousehold summary:")
    print(f"  Total households: {len(households)}")
    print(f"  Avg members per household: {households['member_count'].mean():.1f}")
    
    # Save to Supabase
    print("\nUpdating donor records with household_id...")
    # Update in batches
    for _, row in df[['id', 'household_id', 'address_key']].dropna().iterrows():
        client.table('nc_boe_donations_raw').update({
            'household_id': row['household_id'],
            'address_key': row['address_key']
        }).eq('id', row['id']).execute()
    
    print("Done!")
