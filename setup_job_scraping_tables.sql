-- Create job_scraping_config table
CREATE TABLE IF NOT EXISTS job_scraping_config (
    id UUID NOT NULL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    config JSONB NOT NULL DEFAULT '{}',
    poll_hours INTEGER NOT NULL DEFAULT 24,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    legal_approved BOOLEAN NOT NULL DEFAULT false,
    legal_approval_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_job_scraping_config_source_type ON job_scraping_config(source_type);
CREATE INDEX IF NOT EXISTS ix_job_scraping_config_enabled ON job_scraping_config(enabled);

-- Create scraping_run table
CREATE TABLE IF NOT EXISTS scraping_run (
    id UUID NOT NULL PRIMARY KEY,
    config_id UUID NOT NULL REFERENCES job_scraping_config(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    jobs_found INTEGER NOT NULL DEFAULT 0,
    jobs_processed INTEGER NOT NULL DEFAULT 0,
    jobs_failed INTEGER NOT NULL DEFAULT 0,
    errors JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_scraping_run_status ON scraping_run(status);
CREATE INDEX IF NOT EXISTS ix_scraping_run_config_id ON scraping_run(config_id);

-- Create mass_upload_batch table
CREATE TABLE IF NOT EXISTS mass_upload_batch (
    id UUID NOT NULL PRIMARY KEY,
    upload_type VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    field_mapping JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_rows INTEGER NOT NULL DEFAULT 0,
    processed_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    errors JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_mass_upload_batch_status ON mass_upload_batch(status);
CREATE INDEX IF NOT EXISTS ix_mass_upload_batch_user_id ON mass_upload_batch(user_id);

-- Create job_deduplication table
CREATE TABLE IF NOT EXISTS job_deduplication (
    id UUID NOT NULL PRIMARY KEY,
    fingerprint VARCHAR(256) NOT NULL UNIQUE,
    external_ids JSONB NOT NULL DEFAULT '{}',
    ingest_queue_item_id UUID,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    seen_count INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS ix_job_deduplication_fingerprint ON job_deduplication(fingerprint);
CREATE INDEX IF NOT EXISTS ix_job_deduplication_ingest_queue_item_id ON job_deduplication(ingest_queue_item_id);

-- Create upload_field_mapping table
CREATE TABLE IF NOT EXISTS upload_field_mapping (
    id UUID NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(1000),
    field_mapping JSONB NOT NULL,
    required_fields JSONB NOT NULL DEFAULT '[]',
    is_system BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_upload_field_mapping_name ON upload_field_mapping(name);
CREATE INDEX IF NOT EXISTS ix_upload_field_mapping_is_system ON upload_field_mapping(is_system);

SELECT 'Tables created successfully' as status;
