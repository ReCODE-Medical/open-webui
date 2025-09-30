# Zhealth API Deployment Checklist

## Pre-Deployment

### 1. Environment Configuration
- [ ] Verify `SUPABASE_DATABASE_URL` environment variable is set
- [ ] Test connection to Supabase database
- [ ] Ensure application user has appropriate database permissions

### 2. Database Setup
- [ ] Verify Supabase database is accessible
- [ ] Check that schema creation permissions exist
- [ ] Review database connection pool settings

### 3. Code Review
- [ ] Review `/workspace/backend/open_webui/models/zhealth.py`
- [ ] Review changes to `/workspace/backend/open_webui/main.py`
- [ ] Check for any linter errors or warnings
- [ ] Verify imports are correct

### 4. Testing (Development Environment)
- [ ] Test API key authentication
- [ ] Test successful request/response
- [ ] Test streaming responses
- [ ] Test error handling
- [ ] Verify logs are written to Supabase
- [ ] Check log entry completeness

## Deployment Steps

### 1. Backup
- [ ] Backup current application code
- [ ] Backup Supabase database
- [ ] Document current state

### 2. Deploy Code
- [ ] Deploy updated application files
- [ ] Restart application services
- [ ] Check application logs for startup errors
- [ ] Verify zhealth initialization message in logs

### 3. Database Verification
- [ ] Verify `zhealth` schema was created
  ```sql
  \dn zhealth
  ```
- [ ] Verify `zhealth_logs` table exists
  ```sql
  \dt zhealth.*
  ```
- [ ] Check table structure
  ```sql
  \d zhealth.zhealth_logs
  ```
- [ ] Verify indexes were created
  ```sql
  SELECT indexname FROM pg_indexes WHERE schemaname = 'zhealth';
  ```

### 4. Initial Testing
- [ ] Test health/status endpoint
- [ ] Test authentication with valid API key
- [ ] Test authentication failure (no API key)
- [ ] Test with simple request
- [ ] Verify log entry was created
- [ ] Check all log fields are populated

### 5. Integration Testing
- [ ] Test with actual model
- [ ] Test streaming response
- [ ] Test non-streaming response
- [ ] Test error scenarios
- [ ] Test concurrent requests
- [ ] Verify all data is captured correctly

## Post-Deployment

### 1. Monitoring Setup
- [ ] Set up database space monitoring
- [ ] Configure log aggregation
- [ ] Set up alerts for errors
- [ ] Monitor API response times
- [ ] Track database write performance

### 2. Client Communication
- [ ] Share API documentation with Zhealth team
- [ ] Provide API key to Zhealth team
- [ ] Share quick start guide
- [ ] Provide contact information for support
- [ ] Schedule follow-up meeting

### 3. Documentation
- [ ] Update internal documentation
- [ ] Document deployment date and version
- [ ] Record any configuration changes
- [ ] Update runbooks if needed

### 4. Performance Baseline
- [ ] Record initial performance metrics
- [ ] Document baseline response times
- [ ] Note database size
- [ ] Track request volume

## Verification Commands

### Check Application Logs
```bash
# Look for initialization message
grep "Zhealth table initialized" application.log

# Check for errors
grep -i "failed.*zhealth" application.log

# Monitor real-time
tail -f application.log | grep -i zhealth
```

### Check Database
```sql
-- Verify schema exists
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name = 'zhealth';

-- Verify table exists
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'zhealth';

-- Check initial log count
SELECT COUNT(*) FROM zhealth.zhealth_logs;

-- View recent logs
SELECT id, user_email, model_id, request_timestamp 
FROM zhealth.zhealth_logs 
ORDER BY request_timestamp DESC 
LIMIT 5;
```

### Test API Endpoint
```bash
# Test authentication
curl -X POST https://your-domain.com/api/chat/zhealth/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 401 Unauthorized

# Test with API key
curl -X POST https://your-domain.com/api/chat/zhealth/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 200 OK with response

# Run test script
python test_zhealth_api.py --api-key sk-key --base-url https://your-domain.com
```

## Rollback Plan

If issues occur:

### 1. Application Rollback
```bash
# Stop application
sudo systemctl stop your-app-service

# Restore previous code
git checkout previous-commit

# Restart application
sudo systemctl start your-app-service
```

### 2. Database Rollback (if needed)
```sql
-- Drop the zhealth schema (use with caution!)
DROP SCHEMA IF EXISTS zhealth CASCADE;
```

### 3. Verify Rollback
- [ ] Check application starts successfully
- [ ] Verify standard endpoints still work
- [ ] Document what went wrong
- [ ] Plan fixes before retry

## Post-Launch Monitoring (First 24 Hours)

### Hourly Checks
- [ ] Check application logs for errors
- [ ] Monitor database size growth
- [ ] Check API response times
- [ ] Verify logs are being written
- [ ] Monitor error rates

### Daily Checks (First Week)
- [ ] Review log data completeness
- [ ] Check disk space usage
- [ ] Monitor query performance
- [ ] Collect feedback from Zhealth team
- [ ] Review any issues or questions

## Success Criteria

Deployment is successful when:
- ✅ Application starts without errors
- ✅ Zhealth schema and table exist in Supabase
- ✅ API endpoint responds to requests
- ✅ Authentication works correctly
- ✅ Logs are written to database
- ✅ All log fields are populated
- ✅ Streaming and non-streaming both work
- ✅ Error handling works correctly
- ✅ No performance degradation
- ✅ Zhealth team can access the endpoint

## Issues Log

Use this section to document any issues during deployment:

| Date | Issue | Resolution | Notes |
|------|-------|------------|-------|
|      |       |            |       |

## Sign-Off

- [ ] Development Lead: _________________ Date: _______
- [ ] DevOps: _________________ Date: _______
- [ ] Database Admin: _________________ Date: _______
- [ ] QA: _________________ Date: _______

## Notes

Additional notes about the deployment:

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Version/Commit:** _____________