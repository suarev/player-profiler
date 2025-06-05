# backend/data_pipeline/show_columns.py
from database import DatabaseManager

def show_all_columns():
    """Display all columns for each table"""
    db = DatabaseManager()
    db.connect()
    
    try:
        cursor = db.connection.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'football_data'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            print(f"\n{'='*80}")
            print(f"TABLE: {table}")
            print(f"{'='*80}")
            
            # Get columns
            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_schema = 'football_data' 
                AND table_name = '{table}'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            for col_name, data_type in columns:
                print(f"{col_name:<40} {data_type}")
            
            print(f"\nTotal columns: {len(columns)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    show_all_columns()