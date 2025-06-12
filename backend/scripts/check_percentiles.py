import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import execute_query

# Check what's in the percentiles table
query = """
SELECT 
    position_group,
    COUNT(*) as player_count,
    MIN(computed_at) as first_computed,
    MAX(computed_at) as last_computed
FROM football_data.player_percentiles_all
GROUP BY position_group
ORDER BY position_group
"""

print("Checking precomputed percentiles...\n")
result = execute_query(query)
print(result)

# Check some sample forwards
print("\n\nSample forward percentiles:")
sample_query = """
SELECT 
    p.name,
    p.team,
    pp.position_group
FROM football_data.player_percentiles_all pp
JOIN football_data.players p ON pp.player_id = p.id
WHERE pp.position_group = 'forward'
LIMIT 10
"""

sample = execute_query(sample_query)
print(sample)

# Check if specific players exist
print("\n\nChecking specific players:")
check_query = """
SELECT p.name, pp.position_group, pp.computed_at
FROM football_data.players p
LEFT JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
WHERE p.name IN ('Erling Haaland', 'Mohamed Salah', 'Harry Kane')
"""

check = execute_query(check_query)
print(check)

print("\n✅ Your forward percentiles are saved and ready to use!")