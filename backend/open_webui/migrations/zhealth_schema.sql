-- Zhealth Schema and Table Creation Script
-- This script creates the zhealth schema and logs table in Supabase
-- The application will attempt to create these automatically, but this script
-- can be used for manual setup if needed.

-- Create the zhealth schema
CREATE SCHEMA IF NOT EXISTS zhealth;

-- Create the zhealth_logs table
CREATE TABLE IF NOT EXISTS zhealth.zhealth_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    user_email VARCHAR,
    
    -- Request data
    request_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    model_id VARCHAR,
    request_messages JSONB,
    request_params JSONB,
    
    -- Response data
    response_timestamp TIMESTAMP WITH TIME ZONE,
    response_content TEXT,
    response_model VARCHAR,
    response_tokens JSONB,
    
    -- Citations and sources
    citations JSONB,
    sources JSONB,
    
    -- Middleware events
    middleware_events JSONB,
    
    -- Metadata
    metadata JSONB,
    
    -- Error tracking
    error TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_zhealth_logs_user_id ON zhealth.zhealth_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_zhealth_logs_request_timestamp ON zhealth.zhealth_logs(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_zhealth_logs_model_id ON zhealth.zhealth_logs(model_id);
CREATE INDEX IF NOT EXISTS idx_zhealth_logs_user_email ON zhealth.zhealth_logs(user_email);

-- Create a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION zhealth.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_zhealth_logs_updated_at 
    BEFORE UPDATE ON zhealth.zhealth_logs 
    FOR EACH ROW 
    EXECUTE FUNCTION zhealth.update_updated_at_column();

-- Grant appropriate permissions (adjust as needed for your setup)
-- GRANT USAGE ON SCHEMA zhealth TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON zhealth.zhealth_logs TO your_app_user;