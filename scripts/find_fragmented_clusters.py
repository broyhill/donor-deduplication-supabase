"""Find fragmented identity clusters - donors with multiple master_person_ids."""
import os
import pandas as pd
import psycopg2
from fuzzywuzzy import fuzz
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

def find_duplicate_clusters(conn, similarity_threshold=85):
    """Find potential duplicate identities using fuzzy matching."""
    query = """
        SELECT 
            master_person_id,
            donor_name,
            SPLIT_PART(street_line_1, ' ', 1) as house_number,
            zip_code,
            COUNT(*) AS donation_count
        FROM nc_boe_donations_raw
        WHERE last_name IS NOT NULL
        GROUP BY master_person_id, donor_name, house_number, zip_code
    """
    df = pd.read_sql(query, conn)
    
    clusters = []
    # Group by zip and house number for potential matches
    for (zip_code, house_number), group in df.groupby(['zip_code', 'house_number']):
        if pd.isna(zip_code) or pd.isna(house_number):
            continue
        if len(group) < 2:
            continue
            
        names = group['donor_name'].tolist()
        ids = group['master_person_id'].tolist()
        
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if ids[i] == ids[j]:
                    continue
                score = fuzz.token_set_ratio(names[i], names[j])
                if score >= similarity_threshold:
                    clusters.append({
                        'zip_code': zip_code,
                        'house_number': house_number,
                        'name_1': names[i],
                        'name_2': names[j],
                        'id_1': ids[i],
                        'id_2': ids[j],
                        'similarity': score
                    })
    
    return pd.DataFrame(clusters)

def main():
    conn = get_connection()
    try:
        df = find_duplicate_clusters(conn)
        output_path = 'data/cleaned/merge_candidates.csv'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Found {len(df)} potential duplicate clusters.")
        print(f"Saved to {output_path}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
