-- Create the main schema for our football data
CREATE SCHEMA IF NOT EXISTS football_data;

-- Set the default search path
SET search_path TO football_data, public;

-- Create a simple players table (we'll populate this from scraped data)
CREATE TABLE IF NOT EXISTS football_data.players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_player_name ON football_data.players(name);

-- Grant permissions
GRANT ALL ON SCHEMA football_data TO dev_user;
GRANT ALL ON ALL TABLES IN SCHEMA football_data TO dev_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA football_data TO dev_user;