# Create test_fbref.py
import soccerdata as sd

print("Testing FBref connection...")

try:
    # Test with Premier League current season
    fbref = sd.FBref(leagues=["ENG-Premier League"], seasons=["2024-2025"])
    
    print("Trying to fetch standard stats...")
    df = fbref.read_player_season_stats(stat_type="standard")
    
    print(f"✅ Success! Found {len(df)} player records")
    print(f"Columns: {list(df.columns)[:10]}...")  # Show first 10 columns
    
except Exception as e:
    print(f"❌ Error: {e}")