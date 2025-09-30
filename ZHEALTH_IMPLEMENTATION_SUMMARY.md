# Zhealth API Implementation Summary

## Overview

A new API endpoint has been created specifically for the Zhealth client that provides complete logging and visibility into all API usage. The endpoint stores requests, responses, citations, sources, and middleware events to a dedicated Supabase database.

## What Was Created

### 1. Database Model (`/workspace/backend/open_webui/models/zhealth.py`)

A new SQLAlchemy model for logging Zhealth API interactions:

- **Table**: `zhealth.zhealth_logs` (in the `zhealth` schema)
- **Features**:
  - Automatic schema creation on application startup
  - Full request/response logging
  - Citations and sources tracking
  - Middleware events capture
  - Token usage statistics
  - Error tracking
  - Timestamps for request and response

**Key Classes**:
- `ZhealthLog`: SQLAlchemy ORM model
- `ZhealthLogs`: Static methods for CRUD operations

### 2. API Endpoint (`/workspace/backend/open_webui/main.py`)

A new route added to the main application:

**Endpoint**: `POST /api/chat/zhealth/completions`

**Features**:
- OpenAI-compatible chat completion interface
- Requires API key authentication (same as standard endpoint)
- Automatic logging of all request/response data
- Supports both streaming and non-streaming responses
- Captures citations, sources, and middleware events
- Non-intrusive error handling (logging failures don't break API)

### 3. Database Migration Script (`/workspace/backend/open_webui/migrations/zhealth_schema.sql`)

SQL script for manual database setup if needed:
- Creates `zhealth` schema
- Creates `zhealth_logs` table
- Adds indexes for common queries
- Creates trigger for automatic `updated_at` timestamp

### 4. Documentation (`/workspace/ZHEALTH_API_DOCUMENTATION.md`)

Complete API documentation including:
- Authentication details
- Request/response formats
- Example usage in multiple languages (cURL, Python, JavaScript)
- Database schema details
- Query examples for analyzing logs
- Troubleshooting guide

### 5. Test Script (`/workspace/test_zhealth_api.py`)

Python test script for verifying the implementation:
- Tests authentication requirement
- Tests successful API calls
- Supports streaming and non-streaming modes
- Provides detailed output for debugging

## Files Modified

1. **`/workspace/backend/open_webui/main.py`**
   - Added import for `ZhealthLogs`
   - Added new route `@app.post("/api/chat/zhealth/completions")`

2. **`/workspace/backend/open_webui/models/zhealth.py`** (New file)
   - Complete logging model and helper functions

## Database Schema

### Table: `zhealth.zhealth_logs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | VARCHAR | Authenticated user's ID |
| `user_email` | VARCHAR | User's email address |
| `request_timestamp` | TIMESTAMP | When request was received |
| `model_id` | VARCHAR | Model requested |
| `request_messages` | JSONB | Complete message history |
| `request_params` | JSONB | Request parameters |
| `response_timestamp` | TIMESTAMP | When response completed |
| `response_content` | TEXT | Generated response text |
| `response_model` | VARCHAR | Actual model used |
| `response_tokens` | JSONB | Token usage statistics |
| `citations` | JSONB | Citations in response |
| `sources` | JSONB | Source documents |
| `middleware_events` | JSONB | Processing events |
| `metadata` | JSONB | Additional metadata |
| `error` | TEXT | Error message if failed |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

## How It Works

### Request Flow

1. **Request Received**: Client sends POST to `/api/chat/zhealth/completions` with API key
2. **Authentication**: Standard API key authentication (same as other endpoints)
3. **Initial Log**: Creates log entry in Supabase with request data
4. **Processing**: Processes request through standard chat completion pipeline
5. **Event Capture**: Collects all middleware events during processing
6. **Response Handling**:
   - **Non-streaming**: Extracts response data immediately
   - **Streaming**: Wraps stream to capture data as it flows
7. **Log Update**: Updates Supabase log with response data, citations, sources, events
8. **Response Return**: Returns response to client (identical to standard endpoint)

### Error Handling

- Logging failures do not break API functionality
- Errors are logged with try/catch blocks
- Application continues even if Supabase is unavailable
- All errors are logged to application logs

## Usage Example

```bash
curl -X POST https://your-domain.com/api/chat/zhealth/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-api-key" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "What are the symptoms of diabetes?"}
    ]
  }'
```

## Configuration Requirements

### Environment Variables

Ensure `SUPABASE_DATABASE_URL` is set in your environment:

```bash
export SUPABASE_DATABASE_URL="postgresql://user:pass@host:port/database"
```

### Supabase Setup

The application will automatically:
1. Create the `zhealth` schema if it doesn't exist
2. Create the `zhealth_logs` table
3. Set up proper columns and types

If automatic setup fails, run the migration script manually:

```sql
psql $SUPABASE_DATABASE_URL < backend/open_webui/migrations/zhealth_schema.sql
```

## Testing

### Run the Test Script

```bash
python test_zhealth_api.py \
  --api-key sk-your-api-key \
  --base-url http://localhost:8080
```

### Manual Testing

```bash
# Test with cURL
curl -X POST http://localhost:8080/api/chat/zhealth/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-api-key" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Verify Database Logs

```sql
-- Check that logs are being created
SELECT COUNT(*) FROM zhealth.zhealth_logs;

-- View recent logs
SELECT 
    id,
    user_email,
    model_id,
    request_timestamp,
    response_timestamp,
    LEFT(response_content, 100) as response_preview
FROM zhealth.zhealth_logs
ORDER BY request_timestamp DESC
LIMIT 10;
```

## Differences from Standard Endpoint

| Feature | `/api/chat/completions` | `/api/chat/zhealth/completions` |
|---------|-------------------------|----------------------------------|
| Authentication | API key required | API key required |
| Request format | OpenAI-compatible | OpenAI-compatible |
| Response format | OpenAI-compatible | OpenAI-compatible |
| Database logging | No | **Yes - Complete logging** |
| Citations capture | No | **Yes** |
| Events logging | No | **Yes** |
| Token tracking | No | **Yes** |

## Monitoring and Analytics

### Query Examples

```sql
-- Total requests by user
SELECT 
    user_email,
    COUNT(*) as request_count,
    SUM((response_tokens->>'total_tokens')::int) as total_tokens
FROM zhealth.zhealth_logs
WHERE response_tokens IS NOT NULL
GROUP BY user_email
ORDER BY request_count DESC;

-- Average response time
SELECT 
    model_id,
    COUNT(*) as requests,
    AVG(EXTRACT(EPOCH FROM (response_timestamp - request_timestamp))) as avg_seconds
FROM zhealth.zhealth_logs
WHERE response_timestamp IS NOT NULL
GROUP BY model_id;

-- Error rate
SELECT 
    DATE(request_timestamp) as date,
    COUNT(*) as total_requests,
    SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors,
    ROUND(100.0 * SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate_pct
FROM zhealth.zhealth_logs
GROUP BY DATE(request_timestamp)
ORDER BY date DESC;

-- Most common queries
SELECT 
    request_messages->0->>'content' as first_message,
    COUNT(*) as frequency
FROM zhealth.zhealth_logs
WHERE request_messages IS NOT NULL
GROUP BY request_messages->0->>'content'
ORDER BY frequency DESC
LIMIT 20;
```

## Security Considerations

1. **API Key**: Same authentication as standard endpoint
2. **Data Isolation**: Separate `zhealth` schema isolates client data
3. **Access Control**: Configure Supabase permissions appropriately
4. **Audit Trail**: Complete request/response history for compliance
5. **PII**: User emails and IDs are stored - ensure compliance with privacy regulations

## Maintenance

### Disk Space

The logs table will grow over time. Consider:
- Regular archival of old logs
- Partitioning by date
- Setting up retention policies

```sql
-- Example: Delete logs older than 90 days
DELETE FROM zhealth.zhealth_logs
WHERE request_timestamp < NOW() - INTERVAL '90 days';

-- Or archive to another table
CREATE TABLE zhealth.zhealth_logs_archive AS
SELECT * FROM zhealth.zhealth_logs
WHERE request_timestamp < NOW() - INTERVAL '90 days';
```

### Monitoring

Set up alerts for:
- High error rates
- Slow response times
- Unusual usage patterns
- Logging failures (check application logs)

## Troubleshooting

### Logs Not Appearing

1. Check `SUPABASE_DATABASE_URL` is set correctly
2. Verify Supabase credentials and permissions
3. Check application logs for zhealth warnings
4. Run migration script manually

### Schema Not Created

```sql
-- Manually create schema
CREATE SCHEMA IF NOT EXISTS zhealth;

-- Verify schema exists
\dn zhealth
```

### Permission Errors

```sql
-- Grant permissions to application user
GRANT USAGE ON SCHEMA zhealth TO your_app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA zhealth TO your_app_user;
```

### Application Logs

Check for zhealth-related messages:

```bash
# In application logs, look for:
grep -i zhealth application.log

# Look for initialization:
grep "Zhealth table initialized" application.log

# Look for errors:
grep "Failed to.*zhealth" application.log
```

## Next Steps

1. **Deploy**: Deploy the updated application to your environment
2. **Configure**: Ensure `SUPABASE_DATABASE_URL` is set
3. **Test**: Run the test script to verify functionality
4. **Monitor**: Set up monitoring and alerts
5. **Provide Access**: Share API documentation with Zhealth client
6. **Review**: Regularly review logs for insights and issues

## Support

For questions or issues:
1. Check the application logs
2. Review the troubleshooting section in the documentation
3. Verify database connectivity and permissions
4. Contact your system administrator

---

**Implementation Date**: September 30, 2025
**Status**: Complete and ready for deployment