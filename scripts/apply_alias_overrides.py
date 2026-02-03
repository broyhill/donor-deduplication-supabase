"""Apply alias overrides to unify master_person_id across name variations."""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB', 'postgres'),
        user=os.getenv('SUPABASE_USER', 'postgres'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=os.getenv('SUPABASE_PORT', '5432')
    )

def apply_alias_overrides(conn):
    """Update master_person_id based on person_aliases table."""
    query = """
    UPDATE nc_boe_donations_raw d
    SET master_person_id = a.master_person_id
    FROM person_aliases a
    WHERE UPPER(TRIM(d.donor_name)) = UPPER(TRIM(a.alias_name))
      AND d.master_person_id IS DISTINCT FROM a.master_person_id;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        rows_updated = cur.rowcount
        conn.commit()
        print(f"✅ Alias overrides applied: {rows_updated} records updated.")
    return rows_updated

def main():
    conn = get_connection()
    try:
        apply_alias_overrides(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
