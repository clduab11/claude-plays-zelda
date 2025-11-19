-- Initialize Zelda Analytics Database

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    deaths INTEGER DEFAULT 0,
    enemies_defeated INTEGER DEFAULT 0,
    rooms_explored INTEGER DEFAULT 0,
    items_collected INTEGER DEFAULT 0
);

-- Decisions table
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES sessions(session_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(100) NOT NULL,
    parameters JSONB,
    reasoning TEXT,
    game_state JSONB,
    outcome VARCHAR(50),
    success BOOLEAN
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES sessions(session_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,
    data JSONB,
    priority INTEGER DEFAULT 1
);

-- Game states table (for tracking over time)
CREATE TABLE IF NOT EXISTS game_states (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES sessions(session_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hearts INTEGER,
    max_hearts INTEGER,
    rupees INTEGER,
    location VARCHAR(255),
    enemies_nearby INTEGER,
    items_nearby INTEGER
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_game_states_session ON game_states(session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);

-- Create view for session summaries
CREATE OR REPLACE VIEW session_summaries AS
SELECT
    s.session_id,
    s.started_at,
    s.ended_at,
    s.duration_seconds,
    s.deaths,
    s.enemies_defeated,
    s.rooms_explored,
    s.items_collected,
    COUNT(DISTINCT d.id) as total_decisions,
    COUNT(DISTINCT e.id) as total_events,
    AVG(CASE WHEN d.success THEN 1 ELSE 0 END) as success_rate
FROM sessions s
LEFT JOIN decisions d ON s.session_id = d.session_id
LEFT JOIN events e ON s.session_id = e.session_id
GROUP BY s.id;
