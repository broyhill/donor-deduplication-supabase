#!/usr/bin/env python3
"""
Donor Deduplication Pipeline Runner

Orchestrates the full donor cleaning and deduplication pipeline.
Run steps individually or execute the full pipeline.

Usage:
    python run_pipeline.py --full           # Run entire pipeline
    python run_pipeline.py --step parse     # Run specific step
    python run_pipeline.py --step normalize
    python run_pipeline.py --step spouses
    python run_pipeline.py --step master_ids
"""

import os
import sys
import click
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

# Import pipeline modules
from parse_names import parse_donor_names
from normalize_addresses import normalize_addresses
from infer_spouses import infer_spouse_pairs, add_spouse_info
from assign_master_ids import assign_master_ids

load_dotenv()

def get_supabase_client():
    """Initialize Supabase client from environment variables."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    return create_client(url, key)

def load_raw_donors(client, table='nc_boe_donations_raw', limit=None):
    """Load raw donor data from Supabase."""
    query = client.table(table).select('*')
    if limit:
        query = query.limit(limit)
    response = query.execute()
    return pd.DataFrame(response.data)

def save_to_supabase(client, df, table, upsert_key=None):
    """Save DataFrame to Supabase table."""
    records = df.to_dict('records')
    if upsert_key:
        client.table(table).upsert(records, on_conflict=upsert_key).execute()
    else:
        client.table(table).insert(records).execute()
    print(f"Saved {len(records)} records to {table}")

@click.command()
@click.option('--full', is_flag=True, help='Run full pipeline')
@click.option('--step', type=click.Choice(['parse', 'normalize', 'spouses', 'master_ids']),
              help='Run specific pipeline step')
@click.option('--limit', type=int, default=None, help='Limit records for testing')
@click.option('--dry-run', is_flag=True, help='Print actions without executing')
def main(full, step, limit, dry_run):
    """Run the donor deduplication pipeline."""
    
    if not full and not step:
        click.echo("Specify --full or --step <step_name>")
        sys.exit(1)
    
    client = get_supabase_client()
    
    steps = ['parse', 'normalize', 'spouses', 'master_ids'] if full else [step]
    
    for current_step in steps:
        click.echo(f"\n{'='*50}")
        click.echo(f"Running step: {current_step}")
        click.echo('='*50)
        
        if dry_run:
            click.echo(f"[DRY RUN] Would execute: {current_step}")
            continue
        
        if current_step == 'parse':
            df = load_raw_donors(client, limit=limit)
            df = parse_donor_names(df, name_col='donor_name')
            save_to_supabase(client, df, 'donor_master', upsert_key='id')
            
        elif current_step == 'normalize':
            df = load_raw_donors(client, 'donor_master', limit=limit)
            df = normalize_addresses(df)
            save_to_supabase(client, df, 'donor_master', upsert_key='id')
            
        elif current_step == 'spouses':
            df = load_raw_donors(client, 'donor_master', limit=limit)
            spouse_df = infer_spouse_pairs(df)
            df = add_spouse_info(df, spouse_df)
            save_to_supabase(client, spouse_df, 'donor_spouses')
            save_to_supabase(client, df, 'donor_master', upsert_key='id')
            
        elif current_step == 'master_ids':
            df = load_raw_donors(client, 'donor_master', limit=limit)
            df = assign_master_ids(df)
            save_to_supabase(client, df, 'donor_master', upsert_key='id')
        
        click.echo(f"Completed: {current_step}")
    
    click.echo("\nPipeline finished!")

if __name__ == '__main__':
    main()
