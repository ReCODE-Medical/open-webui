# Zhealth Database Migration

## Overview

This directory contains the database migration script for the Zhealth logging schema.

## File: `zhealth_schema.sql`

This SQL script creates the necessary database structures for logging Zhealth API requests and responses.

### What it creates:

1. **Schema:** `zhealth`
2. **Table:** `zhealth.zhealth_logs`
3. **Indexes:** For user_id, request_timestamp, model_id, user_email
4. **Trigger:** Automatic `updated_at` timestamp

## Automatic Migration

The application will automatically create the schema and table on startup via the `zhealth.py` model file.

**No manual intervention required** for normal deployments.

## Manual Migration

If automatic migration fails or you need to set up the database manually:

### PostgreSQL/Supabase

```bash
# Using psql
psql $SUPABASE_DATABASE_URL < zhealth_schema.sql

# Or connect and run
psql $SUPABASE_DATABASE_URL
\i /path/to/zhealth_schema.sql
```

### Verify Migration

```sql
-- Check schema exists
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name = 'zhealth';

-- Check table exists
\dt zhealth.*

-- Check table structure
\d zhealth.zhealth_logs

-- Check indexes
SELECT indexname FROM pg_indexes 
WHERE schemaname = 'zhealth';
```

## Rollback

To remove the zhealth schema and all its tables:

```sql
DROP SCHEMA IF EXISTS zhealth CASCADE;
```

**⚠️ Warning:** This will delete all logged data!

## Permissions

Ensure your application database user has appropriate permissions:

```sql
-- Grant schema usage
GRANT USAGE ON SCHEMA zhealth TO your_app_user;

-- Grant table access
GRANT SELECT, INSERT, UPDATE ON zhealth.zhealth_logs TO your_app_user;

-- Grant sequence access (for auto-increment, if any)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA zhealth TO your_app_user;
```

## Maintenance

### Archival

Consider archiving old logs periodically:

```sql
-- Archive logs older than 90 days
CREATE TABLE zhealth.zhealth_logs_archive AS
SELECT * FROM zhealth.zhealth_logs
WHERE request_timestamp < NOW() - INTERVAL '90 days';

DELETE FROM zhealth.zhealth_logs
WHERE request_timestamp < NOW() - INTERVAL '90 days';
```

### Vacuum

Periodically vacuum the table to reclaim space:

```sql
VACUUM ANALYZE zhealth.zhealth_logs;
```

## Troubleshooting

### Permission Denied

```sql
-- Grant all necessary permissions
GRANT ALL PRIVILEGES ON SCHEMA zhealth TO your_app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA zhealth TO your_app_user;
```

### Schema Already Exists

This is normal - the script uses `CREATE SCHEMA IF NOT EXISTS`, so it's safe to run multiple times.

### Table Already Exists

This is normal - the script uses `CREATE TABLE IF NOT EXISTS`, so it's safe to run multiple times.

## Schema Version

**Version:** 1.0  
**Created:** 2025-09-30  
**Purpose:** Initial Zhealth logging schema

## Related Files

- Model: `/workspace/backend/open_webui/models/zhealth.py`
- Endpoint: `/workspace/backend/open_webui/main.py` (zhealth_chat_completion function)
- Documentation: `/workspace/ZHEALTH_*.md`