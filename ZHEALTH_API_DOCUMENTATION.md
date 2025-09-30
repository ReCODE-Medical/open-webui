# Zhealth API Documentation

## Overview

The Zhealth API endpoint provides complete logging and visibility into API usage for the Zhealth client. This endpoint automatically captures and stores all requests, responses, citations, sources, and middleware events to a dedicated Supabase database.

## Endpoint

```
POST /api/chat/zhealth/completions
```

## Authentication

This endpoint requires API key authentication via the Bearer token in the Authorization header:

```bash
Authorization: Bearer sk-your-api-key-here
```

## Request Format

The request format is identical to the standard `/api/chat/completions` endpoint:

```json
{
  "model": "model-id",
  "messages": [
    {
      "role": "user",
      "content": "Your question here"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1.0,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
```

## Response Format

The response format is identical to the standard OpenAI-compatible chat completion response.

## Database Logging

All requests and responses through this endpoint are automatically logged to the `zhealth.zhealth_logs` table in Supabase with the following information:

### Request Data
- `user_id` - The authenticated user's ID
- `user_email` - The authenticated user's email
- `request_timestamp` - When the request was received
- `model_id` - The model used for the request
- `request_messages` - The complete message history sent
- `request_params` - All request parameters (temperature, max_tokens, etc.)

### Response Data
- `response_timestamp` - When the response was completed
- `response_content` - The generated response text
- `response_model` - The actual model that generated the response
- `response_tokens` - Token usage statistics (prompt tokens, completion tokens, total tokens)

### Additional Context
- `citations` - Any citations included in the response
- `sources` - Source documents or references used
- `middleware_events` - All middleware processing events
- `metadata` - Additional metadata about the request/response
- `error` - Any error messages if the request failed

### Timestamps
- `created_at` - When the log entry was created
- `updated_at` - When the log entry was last updated

## Example Usage

### Using cURL

```bash
curl -X POST https://your-domain.com/api/chat/zhealth/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-api-key-here" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "What are the symptoms of diabetes?"
      }
    ],
    "stream": false
  }'
```

### Using Python

```python
import requests

url = "https://your-domain.com/api/chat/zhealth/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-your-api-key-here"
}
data = {
    "model": "gpt-4",
    "messages": [
        {
            "role": "user",
            "content": "What are the symptoms of diabetes?"
        }
    ],
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(result)
```

### Using JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

const url = 'https://your-domain.com/api/chat/zhealth/completions';
const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk-your-api-key-here'
};
const data = {
    model: 'gpt-4',
    messages: [
        {
            role: 'user',
            content: 'What are the symptoms of diabetes?'
        }
    ],
    stream: false
};

fetch(url, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => console.log(result))
.catch(error => console.error('Error:', error));
```

## Querying the Logs

You can query the logs directly from your Supabase database:

```sql
-- Get all logs for a specific user
SELECT * FROM zhealth.zhealth_logs
WHERE user_email = 'user@zhealth.com'
ORDER BY request_timestamp DESC;

-- Get logs with errors
SELECT * FROM zhealth.zhealth_logs
WHERE error IS NOT NULL
ORDER BY request_timestamp DESC;

-- Get token usage statistics
SELECT 
    model_id,
    COUNT(*) as request_count,
    SUM((response_tokens->>'total_tokens')::int) as total_tokens
FROM zhealth.zhealth_logs
WHERE response_tokens IS NOT NULL
GROUP BY model_id;

-- Get logs from a specific time period
SELECT * FROM zhealth.zhealth_logs
WHERE request_timestamp BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY request_timestamp DESC;

-- Get logs with citations
SELECT 
    id,
    user_email,
    request_timestamp,
    model_id,
    jsonb_array_length(citations) as citation_count
FROM zhealth.zhealth_logs
WHERE citations IS NOT NULL AND jsonb_array_length(citations) > 0
ORDER BY request_timestamp DESC;
```

## Database Setup

The database schema is automatically created when the application starts. However, if manual setup is needed, you can run the SQL script located at:

```
backend/open_webui/migrations/zhealth_schema.sql
```

## Features

### Automatic Logging
- Every request is logged before processing begins
- Response data is captured and stored after completion
- Errors are logged if any occur during processing

### Streaming Support
- Supports both streaming and non-streaming responses
- For streaming responses, the complete response is assembled and logged after the stream completes

### Complete Visibility
- Full request and response data
- All middleware events during processing
- Citations and sources from retrieval systems
- Token usage for billing and monitoring
- Error tracking for debugging

### Non-Intrusive
- Logging failures do not affect API functionality
- The endpoint continues to work even if logging fails
- Errors are logged but the request is still processed

## Differences from Standard Endpoint

The main differences between `/api/chat/zhealth/completions` and `/api/chat/completions`:

1. **Complete Logging**: Every aspect of the request/response is logged to Supabase
2. **Dedicated Schema**: Uses the `zhealth` schema for data isolation
3. **Same Functionality**: All other features and behaviors are identical
4. **Same Authentication**: Uses the same API key authentication mechanism

## Security Notes

- API keys are required for authentication
- All data is stored in Supabase with your configured security settings
- User information (ID and email) is logged for tracking purposes
- Ensure your Supabase database has appropriate access controls configured

## Troubleshooting

### Logging Not Working

If logs are not appearing in the database:

1. Check that `SUPABASE_DATABASE_URL` environment variable is set correctly
2. Verify the zhealth schema exists in your Supabase database
3. Check application logs for any zhealth-related warnings or errors
4. Manually run the migration script if the schema wasn't auto-created

### Schema Not Created

If the schema is not automatically created:

```sql
-- Manually create the schema and tables
\i backend/open_webui/migrations/zhealth_schema.sql
```

### Permission Errors

If you encounter permission errors:

```sql
-- Grant necessary permissions
GRANT USAGE ON SCHEMA zhealth TO your_app_user;
GRANT SELECT, INSERT, UPDATE ON zhealth.zhealth_logs TO your_app_user;
```

## Support

For issues or questions, please refer to the main application documentation or contact your system administrator.