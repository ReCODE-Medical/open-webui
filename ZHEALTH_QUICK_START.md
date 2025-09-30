# Zhealth API - Quick Start Guide

## For Zhealth Client Team

This guide provides everything you need to start using the new Zhealth API endpoint.

## What's Different?

You now have a dedicated API endpoint that:
- ✅ Automatically logs **every** request and response
- ✅ Captures all **citations** and **sources**
- ✅ Records all **middleware events** during processing
- ✅ Tracks **token usage** for billing/monitoring
- ✅ Provides **complete visibility** into your API usage

## Your Endpoint

```
POST https://your-domain.com/api/chat/zhealth/completions
```

## Authentication

Use your existing API key in the Authorization header:

```
Authorization: Bearer sk-your-api-key-here
```

## Quick Example

### Python

```python
import requests

response = requests.post(
    "https://your-domain.com/api/chat/zhealth/completions",
    headers={
        "Authorization": "Bearer sk-your-api-key",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What are the symptoms of diabetes?"}
        ]
    }
)

print(response.json())
```

### cURL

```bash
curl -X POST https://your-domain.com/api/chat/zhealth/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "What are the symptoms of diabetes?"}
    ]
  }'
```

### JavaScript

```javascript
const response = await fetch('https://your-domain.com/api/chat/zhealth/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4',
    messages: [
      {role: 'user', content: 'What are the symptoms of diabetes?'}
    ]
  })
});

const data = await response.json();
console.log(data);
```

## Request Format (OpenAI Compatible)

```json
{
  "model": "model-name",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Your question here"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

## Response Format

Standard OpenAI format:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The response text..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

## What Gets Logged?

Every request automatically logs:

1. **Request Details**
   - User ID and email
   - Timestamp
   - Model requested
   - All messages
   - All parameters

2. **Response Details**
   - Complete response text
   - Token usage
   - Timestamp
   - Model used

3. **Context**
   - Citations (if any)
   - Sources (if any)
   - Middleware processing events
   - Any errors

## Accessing Your Logs

Your team will have access to query the logs in Supabase:

```sql
-- View your recent requests
SELECT * FROM zhealth.zhealth_logs
WHERE user_email = 'your@email.com'
ORDER BY request_timestamp DESC
LIMIT 10;

-- Check token usage
SELECT 
    DATE(request_timestamp) as date,
    COUNT(*) as requests,
    SUM((response_tokens->>'total_tokens')::int) as total_tokens
FROM zhealth.zhealth_logs
WHERE user_email = 'your@email.com'
GROUP BY DATE(request_timestamp);
```

## Migration from Old Endpoint

If you're currently using `/api/chat/completions`:

**Old:**
```
POST /api/chat/completions
```

**New (with logging):**
```
POST /api/chat/zhealth/completions
```

Everything else stays the same:
- Same API key
- Same request format
- Same response format
- Same features

## Streaming Support

Yes! Streaming works exactly the same:

```python
response = requests.post(
    "https://your-domain.com/api/chat/zhealth/completions",
    headers={"Authorization": "Bearer sk-key"},
    json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True  # Enable streaming
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## Features

- ✅ **Same API** as standard endpoint
- ✅ **Same authentication** method
- ✅ **Same response format**
- ✅ **Plus complete logging** to database
- ✅ **Streaming supported**
- ✅ **All models supported**

## Testing

Test that everything works:

```bash
# Download test script
curl -O https://your-domain.com/test_zhealth_api.py

# Run test
python test_zhealth_api.py \
  --api-key sk-your-api-key \
  --base-url https://your-domain.com
```

## Troubleshooting

### 401 Unauthorized
- Check your API key is correct
- Ensure `Authorization: Bearer sk-...` header is included

### 404 Not Found
- Verify the URL is correct: `/api/chat/zhealth/completions`
- Check the base URL is correct

### 500 Internal Server Error
- Contact your administrator
- Check application logs

## Support

For issues:
1. Check this guide
2. Review the full documentation in `ZHEALTH_API_DOCUMENTATION.md`
3. Contact your administrator

## Next Steps

1. ✅ Get your API key from administrator
2. ✅ Test with the example above
3. ✅ Update your application to use the new endpoint
4. ✅ Monitor your usage via the logs

---

**Questions?** Contact your system administrator.

**Full Documentation:** See `ZHEALTH_API_DOCUMENTATION.md`