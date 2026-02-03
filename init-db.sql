-- ==========================================
-- HARDWARE PIPELINE DATABASE SCHEMA
-- PostgreSQL 15+
-- ==========================================

-- Set timezone
SET timezone = 'Asia/Kolkata';

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==========================================
-- TABLE: component_cache
-- Stores scraped component data from DigiKey/Mouser
-- ==========================================
CREATE TABLE IF NOT EXISTS component_cache (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    manufacturer VARCHAR(100),
    description TEXT,
    category VARCHAR(50) NOT NULL,
    datasheet_url TEXT,
    specifications JSONB DEFAULT '{}',
    pricing JSONB DEFAULT '{}',
    availability JSONB DEFAULT '{}',
    lifecycle_status VARCHAR(20) DEFAULT 'Active',
    compliance JSONB DEFAULT '{}',
    cached_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 days'),
    source VARCHAR(50) NOT NULL,
    search_term VARCHAR(200),
    scrape_metadata JSONB DEFAULT '{}',
    
    -- Indexes for performance
    CONSTRAINT valid_lifecycle CHECK (lifecycle_status IN ('Active', 'NRND', 'Obsolete', 'Unknown'))
);

CREATE INDEX idx_component_cache_part_number ON component_cache(part_number);
CREATE INDEX idx_component_cache_category ON component_cache(category);
CREATE INDEX idx_component_cache_lifecycle ON component_cache(lifecycle_status);
CREATE INDEX idx_component_cache_expires ON component_cache(expires_at);
CREATE INDEX idx_component_cache_search_term ON component_cache USING gin(search_term gin_trgm_ops);
CREATE INDEX idx_component_cache_description ON component_cache USING gin(description gin_trgm_ops);

COMMENT ON TABLE component_cache IS 'Cache for component data from DigiKey, Mouser, etc. with 30-day TTL';

-- ==========================================
-- TABLE: projects
-- Master project table
-- ==========================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    system_type VARCHAR(50) NOT NULL,
    requirements TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'in_progress',
    phase_completed INTEGER DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('in_progress', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_phase CHECK (phase_completed >= 0 AND phase_completed <= 8)
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_system_type ON projects(system_type);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);

COMMENT ON TABLE projects IS 'Master project tracking table';

-- ==========================================
-- TABLE: phase_outputs
-- Stores outputs from each workflow phase
-- ==========================================
CREATE TABLE IF NOT EXISTS phase_outputs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_number INTEGER NOT NULL,
    phase_name VARCHAR(100) NOT NULL,
    output_files JSONB DEFAULT '{}',
    execution_time INTEGER, -- in seconds
    ai_provider VARCHAR(20),
    ai_model VARCHAR(100),
    ai_tokens_used INTEGER DEFAULT 0,
    ai_cost DECIMAL(10,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    error_log TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    CONSTRAINT valid_phase_status CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    CONSTRAINT valid_phase_number CHECK (phase_number >= 1 AND phase_number <= 8)
);

CREATE INDEX idx_phase_outputs_project_id ON phase_outputs(project_id);
CREATE INDEX idx_phase_outputs_phase_number ON phase_outputs(phase_number);
CREATE INDEX idx_phase_outputs_status ON phase_outputs(status);

COMMENT ON TABLE phase_outputs IS 'Tracks outputs and metrics for each workflow phase';

-- ==========================================
-- TABLE: compliance_records
-- Stores compliance check results
-- ==========================================
CREATE TABLE IF NOT EXISTS compliance_records (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) NOT NULL,
    standard VARCHAR(50) NOT NULL,
    compliant BOOLEAN DEFAULT NULL,
    certificate_number VARCHAR(100),
    certificate_url TEXT,
    expiry_date DATE,
    notes TEXT,
    checked_at TIMESTAMP DEFAULT NOW(),
    source VARCHAR(100),
    
    UNIQUE(part_number, standard)
);

CREATE INDEX idx_compliance_part_standard ON compliance_records(part_number, standard);
CREATE INDEX idx_compliance_standard ON compliance_records(standard);
CREATE INDEX idx_compliance_compliant ON compliance_records(compliant);

COMMENT ON TABLE compliance_records IS 'RoHS, REACH, CE, FCC compliance records';

-- ==========================================
-- TABLE: api_usage
-- Tracks AI API usage and costs
-- ==========================================
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    phase_number INTEGER,
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(100) NOT NULL,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    request_metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_usage_provider ON api_usage(provider);
CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp DESC);
CREATE INDEX idx_api_usage_project_id ON api_usage(project_id);
CREATE INDEX idx_api_usage_success ON api_usage(success);

COMMENT ON TABLE api_usage IS 'Tracks AI API usage for billing and analytics';

-- ==========================================
-- TABLE: component_recommendations
-- Caches AI component recommendations
-- ==========================================
CREATE TABLE IF NOT EXISTS component_recommendations (
    id SERIAL PRIMARY KEY,
    requirement_hash VARCHAR(64) UNIQUE NOT NULL,
    system_type VARCHAR(50),
    component_category VARCHAR(50),
    recommended_parts JSONB NOT NULL,
    rationale TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    usage_count INTEGER DEFAULT 1,
    last_used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_recommendations_requirement_hash ON component_recommendations(requirement_hash);
CREATE INDEX idx_recommendations_system_type ON component_recommendations(system_type);
CREATE INDEX idx_recommendations_category ON component_recommendations(component_category);

COMMENT ON TABLE component_recommendations IS 'Caches AI recommendations to reduce API calls';

-- ==========================================
-- TABLE: block_diagrams
-- Stores generated block diagrams
-- ==========================================
CREATE TABLE IF NOT EXISTS block_diagrams (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    diagram_data JSONB NOT NULL,
    diagram_type VARCHAR(50) DEFAULT 'hardware_block_diagram',
    created_at TIMESTAMP DEFAULT NOW(),
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    
    UNIQUE(project_id, version)
);

CREATE INDEX idx_block_diagrams_project_id ON block_diagrams(project_id);
CREATE INDEX idx_block_diagrams_approved ON block_diagrams(approved);

COMMENT ON TABLE block_diagrams IS 'Version-controlled block diagrams for each project';

-- ==========================================
-- TABLE: bom_items
-- Bill of Materials items
-- ==========================================
CREATE TABLE IF NOT EXISTS bom_items (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ref_designator VARCHAR(20) NOT NULL,
    part_number VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    description TEXT,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2),
    extended_price DECIMAL(10,2),
    category VARCHAR(50),
    supplier VARCHAR(50),
    lead_time_days INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(project_id, ref_designator)
);

CREATE INDEX idx_bom_items_project_id ON bom_items(project_id);
CREATE INDEX idx_bom_items_part_number ON bom_items(part_number);
CREATE INDEX idx_bom_items_category ON bom_items(category);

COMMENT ON TABLE bom_items IS 'Bill of Materials line items for each project';

-- ==========================================
-- TABLE: scraping_queue
-- Queue for component scraping tasks
-- ==========================================
CREATE TABLE IF NOT EXISTS scraping_queue (
    id SERIAL PRIMARY KEY,
    search_term VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    results_count INTEGER DEFAULT 0,
    
    CONSTRAINT valid_scraping_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

CREATE INDEX idx_scraping_queue_status ON scraping_queue(status);
CREATE INDEX idx_scraping_queue_priority ON scraping_queue(priority DESC);
CREATE INDEX idx_scraping_queue_created_at ON scraping_queue(created_at);

COMMENT ON TABLE scraping_queue IS 'Queue for managing component scraping tasks';

-- ==========================================
-- TABLE: system_logs
-- General system activity logs
-- ==========================================
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(10) NOT NULL,
    log_source VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    user_id VARCHAR(100),
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_log_source ON system_logs(log_source);
CREATE INDEX idx_system_logs_project_id ON system_logs(project_id);

COMMENT ON TABLE system_logs IS 'System-wide activity and error logs';

-- ==========================================
-- VIEWS
-- ==========================================

-- View: project_summary
CREATE OR REPLACE VIEW project_summary AS
SELECT 
    p.id,
    p.project_name,
    p.user_id,
    p.system_type,
    p.status,
    p.phase_completed,
    p.total_cost,
    p.created_at,
    p.updated_at,
    COUNT(DISTINCT po.id) as total_phase_outputs,
    COUNT(DISTINCT bi.id) as total_bom_items,
    SUM(au.cost) as total_ai_cost,
    SUM(au.tokens_input + au.tokens_output) as total_tokens_used
FROM projects p
LEFT JOIN phase_outputs po ON p.id = po.project_id
LEFT JOIN bom_items bi ON p.id = bi.project_id
LEFT JOIN api_usage au ON p.id = au.project_id
GROUP BY p.id;

COMMENT ON VIEW project_summary IS 'High-level project statistics and metrics';

-- View: component_cache_stats
CREATE OR REPLACE VIEW component_cache_stats AS
SELECT 
    category,
    lifecycle_status,
    source,
    COUNT(*) as component_count,
    COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active_cache_count,
    MAX(cached_at) as last_cached_at
FROM component_cache
GROUP BY category, lifecycle_status, source
ORDER BY category, source;

COMMENT ON VIEW component_cache_stats IS 'Component cache statistics by category and source';

-- ==========================================
-- FUNCTIONS
-- ==========================================

-- Function: update_updated_at_column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates updated_at timestamp';

-- Function: calculate_bom_total
CREATE OR REPLACE FUNCTION calculate_bom_total(p_project_id INTEGER)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    total DECIMAL(10,2);
BEGIN
    SELECT COALESCE(SUM(extended_price), 0)
    INTO total
    FROM bom_items
    WHERE project_id = p_project_id;
    
    -- Update project total cost
    UPDATE projects
    SET total_cost = total
    WHERE id = p_project_id;
    
    RETURN total;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_bom_total(INTEGER) IS 'Calculates and updates total BOM cost for a project';

-- Function: clean_expired_cache
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM component_cache
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO system_logs (log_level, log_source, message, details)
    VALUES ('INFO', 'database_maintenance', 'Cleaned expired component cache', 
            jsonb_build_object('deleted_count', deleted_count));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clean_expired_cache() IS 'Removes expired component cache entries';

-- ==========================================
-- TRIGGERS
-- ==========================================

-- Trigger: update_projects_updated_at
CREATE TRIGGER update_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger: update_bom_extended_price
CREATE OR REPLACE FUNCTION update_bom_extended_price()
RETURNS TRIGGER AS $$
BEGIN
    NEW.extended_price = NEW.unit_price * NEW.quantity;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_bom_extended_price
BEFORE INSERT OR UPDATE OF unit_price, quantity ON bom_items
FOR EACH ROW
EXECUTE FUNCTION update_bom_extended_price();

-- ==========================================
-- SEED DATA (Optional - for testing)
-- ==========================================

-- Insert sample compliance standards
INSERT INTO compliance_records (part_number, standard, compliant, notes, source)
VALUES 
    ('SAMPLE-PART-001', 'RoHS', TRUE, 'Lead-free', 'Manual entry'),
    ('SAMPLE-PART-001', 'REACH', TRUE, 'SVHC compliant', 'Manual entry')
ON CONFLICT (part_number, standard) DO NOTHING;

-- Insert sample component categories
INSERT INTO component_cache (
    part_number, manufacturer, description, category, 
    lifecycle_status, source, search_term
)
VALUES 
    ('SAMPLE-MCU-001', 'STMicroelectronics', 'STM32F407VGT6 ARM Cortex-M4 MCU', 'processor', 'Active', 'DigiKey', 'STM32F4'),
    ('SAMPLE-REG-001', 'Texas Instruments', 'TPS54340 3A Buck Converter', 'power_regulator', 'Active', 'DigiKey', 'buck converter 3.3V'),
    ('SAMPLE-ETH-001', 'Microchip', 'KSZ8081RNA Ethernet PHY', 'interface', 'Active', 'Mouser', 'ethernet phy')
ON CONFLICT (part_number) DO NOTHING;

-- ==========================================
-- MAINTENANCE SCHEDULED JOBS
-- ==========================================

-- Note: Requires pg_cron extension (optional)
-- To enable: CREATE EXTENSION pg_cron;

-- Clean expired cache daily at 2 AM
-- SELECT cron.schedule('clean_expired_cache', '0 2 * * *', 'SELECT clean_expired_cache();');

-- ==========================================
-- GRANTS AND PERMISSIONS
-- ==========================================

-- Grant permissions to n8n user (if different from postgres)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO n8n_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO n8n_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO n8n_user;

-- ==========================================
-- VACUUM AND ANALYZE
-- ==========================================
VACUUM ANALYZE;

-- ==========================================
-- COMPLETION MESSAGE
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Hardware Pipeline Database Initialized';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tables created: 11';
    RAISE NOTICE 'Views created: 2';
    RAISE NOTICE 'Functions created: 3';
    RAISE NOTICE 'Triggers created: 2';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Database ready for Hardware Pipeline Phase 1';
    RAISE NOTICE '============================================';
END $$;
