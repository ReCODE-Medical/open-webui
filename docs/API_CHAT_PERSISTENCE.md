# API Chat Persistence Documentation

## Overview

This directory contains comprehensive documentation for properly persisting chats via the API so they display correctly in the Open WebUI interface.

## Problem

When using the API to create chats, the chat titles appear in the UI history but fail to open properly. This is because the API endpoints don't automatically create complete message structures that the UI requires.

## Solution Documentation

All documentation files are located in the root directory:

### 📖 Getting Started
- **[API_CHAT_SOLUTION_INDEX.md](../API_CHAT_SOLUTION_INDEX.md)** - Start here! Complete index and navigation guide
- **[API_CHAT_CHEATSHEET.md](../API_CHAT_CHEATSHEET.md)** - Quick reference for implementation

### 📚 Detailed Guides
- **[README_API_CHAT_SOLUTION.md](../README_API_CHAT_SOLUTION.md)** - Main overview and quick start
- **[API_CHAT_FIX_SUMMARY.md](../API_CHAT_FIX_SUMMARY.md)** - Executive summary of the issue
- **[API_CHAT_PERSISTENCE_GUIDE.md](../API_CHAT_PERSISTENCE_GUIDE.md)** - Comprehensive step-by-step guide
- **[MESSAGE_STRUCTURE_DIAGRAM.md](../MESSAGE_STRUCTURE_DIAGRAM.md)** - Visual guide to message structure

### 🧪 Test Scripts
- **[test_api_chat_persistence.sh](../test_api_chat_persistence.sh)** - Bash test script
- **[test_api_chat_persistence.py](../test_api_chat_persistence.py)** - Python test script

## Quick Start

### Run Test Scripts

```bash
# Bash version
./test_api_chat_persistence.sh

# Python version
python3 test_api_chat_persistence.py
```

### Python Example

```python
import requests, uuid, time

API = "https://your-instance.com"
TOKEN = "your-token"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1. Create chat
chat = requests.post(f"{API}/api/v1/chats/new", headers=headers,
    json={"chat": {"title": "My Chat", "history": {"messages": {}}}}).json()

# 2. Store complete user message
user_id = str(uuid.uuid4())
asst_id = str(uuid.uuid4())
ts = int(time.time())

requests.post(f"{API}/api/v1/chats/{chat['id']}/messages/{user_id}", headers=headers, json={
    "id": user_id, "parentId": None, "childrenIds": [], "role": "user",
    "content": "Your question", "timestamp": ts, "models": ["model-id"]
})

# 3. Get assistant response
resp = requests.post(f"{API}/api/chat/completions", headers=headers, json={
    "model": "model-id", "chat_id": chat['id'], "id": asst_id,
    "messages": [{"role": "user", "content": "Your question"}]
}).json()

content = resp["choices"][0]["message"]["content"]

# 4. Update user message with link
requests.post(f"{API}/api/v1/chats/{chat['id']}/messages/{user_id}", headers=headers, json={
    "id": user_id, "parentId": None, "childrenIds": [asst_id], "role": "user",
    "content": "Your question", "timestamp": ts, "models": ["model-id"]
})

# 5. Store complete assistant message
requests.post(f"{API}/api/v1/chats/{chat['id']}/messages/{asst_id}", headers=headers, json={
    "id": asst_id, "parentId": user_id, "childrenIds": [], "role": "assistant",
    "content": content, "model": "model-id", "modelName": "Model Name",
    "modelIdx": 0, "timestamp": ts, "done": True
})
```

## Key Points

1. **Generate proper UUIDs** - Use UUID v4 format
2. **Store complete message structures** - Include all required fields
3. **Extract assistant content** - The completions endpoint returns content but doesn't save it
4. **Link messages** - Use `parentId` and `childrenIds`
5. **Use Unix epoch seconds** - For timestamps

## Required Fields

### User Message
- `id` - UUID v4
- `parentId` - Previous message ID or null
- `childrenIds` - Array of next message IDs
- `role` - "user"
- `content` - Message text
- `timestamp` - Unix epoch seconds
- `models` - Array of model IDs

### Assistant Message
- `id` - UUID v4
- `parentId` - User message ID
- `childrenIds` - Array (usually empty)
- `role` - "assistant"
- `content` - Response text (extracted from API response)
- `model` - Model ID
- `modelName` - Human-readable name
- `modelIdx` - Usually 0
- `timestamp` - Unix epoch seconds
- `done` - true

## Related Backend Code

- Chat routes: `backend/open_webui/routers/chats.py`
- Completions endpoint: `backend/open_webui/main.py:1372-1512`
- Message persistence: `backend/open_webui/models/chats.py:312-337`
- Response processing: `backend/open_webui/utils/middleware.py`
- UI message conversion: `src/lib/utils/index.ts:191-222`

## Support

For detailed documentation, troubleshooting, and examples, see the files linked above or start with [API_CHAT_SOLUTION_INDEX.md](../API_CHAT_SOLUTION_INDEX.md).

---

**Note:** This is a workaround for the current API behavior. A proper fix would be to enhance the `/api/chat/completions` endpoint to automatically handle complete message persistence.