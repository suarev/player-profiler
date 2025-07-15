# backend/check_column_existence.py
import psycopg2
import os

db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

print("🔍 COMPLETE COLUMN INVENTORY")
print("="*80)

# Get all tables and their columns
cur.execute("""
    SELECT 
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'football_data'
    AND table_name NOT IN ('players', 'player_percentiles_all')
    ORDER BY table_name, ordinal_position
""")

current_table = None
all_columns = {}

for row in cur.fetchall():
    table, column, dtype = row
    
    if table != current_table:
        if current_table:
            print(f"\nTotal columns: {len(all_columns[current_table])}")
        current_table = table
        all_columns[table] = []
        print(f"\n{'='*80}")
        print(f"TABLE: {table}")
        print(f"{'='*80}")
    
    all_columns[table].append(column)
    print(f"{column:<40} {dtype}")

# Check which defense/misc/possession columns we need
print("\n\n🔍 CHECKING FOR REQUIRED COLUMNS")
print("="*80)

REQUIRED_COLUMNS = {
    'defense': ['tackles_tkl', 'tackles_tklw', 'tackles_def_3rd', 'tackles_att_3rd', 'int', 'blocks_blocks', 'blocks_pass', 'err', 'clr', 'challenges_lost'],
    'possession': ['touches_touches', 'touches_def_3rd', 'touches_att_3rd', 'touches_att_pen', 'carries_prgc', 'carries_cpa', 'carries_1_per_3', 'carries_mis', 'take_ons_succ', 'receiving_rec'],
    'misc': ['performance_crdy', 'performance_crdr', 'performance_fls', 'performance_og', 'performance_recov', 'aerial_duels_won', 'aerial_duels_wonpct']
}

# Find where these columns might be
for category, needed_cols in REQUIRED_COLUMNS.items():
    print(f"\n{category.upper()} columns needed:")
    for col in needed_cols:
        found = False
        for table, columns in all_columns.items():
            if col in columns:
                print(f"  ✅ {col} -> found in {table}")
                found = True
                break
        if not found:
            print(f"  ❌ {col} -> NOT FOUND")

conn.close()