# backend/data_pipeline/test_imports.py
print("Testing imports...")

try:
    import soccerdata as sd
    print("✅ soccerdata imported successfully")
except Exception as e:
    print(f"❌ soccerdata import failed: {e}")

try:
    import ScraperFC as sfc
    print("✅ ScraperFC imported successfully")
except Exception as e:
    print(f"❌ ScraperFC import failed: {e}")

try:
    import psycopg2
    print("✅ psycopg2 imported successfully")
except Exception as e:
    print(f"❌ psycopg2 import failed: {e}")

try:
    import pandas as pd
    print("✅ pandas imported successfully")
except Exception as e:
    print(f"❌ pandas import failed: {e}")