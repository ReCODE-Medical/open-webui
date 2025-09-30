# API Chat Persistence Cheatsheet

## The Problem in One Sentence
The `/api/chat/completions` endpoint doesn't automatically save complete message structures - you must manually store all required fields including the assistant response content.

## Quick Fix Template (Python)

```python
import requests, uuid, time

API = "https://chat.recodemedical.com"
TOKEN = "your-token"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1. Create chat
chat = requests.post(f"{API}/api/v1/chats/new", headers=headers, 
    json={"chat": {"title": "My Chat", "history": {"messages": {}}}}).json()
chat_id = chat["id"]

# 2. Generate IDs
user_id = str(uuid.uuid4())
asst_id = str(uuid.uuid4())
ts = int(time.time())

# 3. Store user message
requests.post(f"{API}/api/v1/chats/{chat_id}/messages/{user_id}", headers=headers, json={
    "id": user_id, "parentId": None, "childrenIds": [], "role": "user",
    "content": "Your question", "timestamp": ts, "models": ["recode-cardio-openai"]
})

# 4. Get response
resp = requests.post(f"{API}/api/chat/completions", headers=headers, json={
    "model": "recode-cardio-openai", "chat_id": chat_id, "id": asst_id,
    "messages": [{"role": "user", "content": "Your question"}]
}).json()
content = resp["choices"][0]["message"]["content"]

# 5. Update user message
requests.post(f"{API}/api/v1/chats/{chat_id}/messages/{user_id}", headers=headers, json={
    "id": user_id, "parentId": None, "childrenIds": [asst_id], "role": "user",
    "content": "Your question", "timestamp": ts, "models": ["recode-cardio-openai"]
})

# 6. Store assistant message
requests.post(f"{API}/api/v1/chats/{chat_id}/messages/{asst_id}", headers=headers, json={
    "id": asst_id, "parentId": user_id, "childrenIds": [], "role": "assistant",
    "content": content, "model": "recode-cardio-openai", "modelName": "Cardiology",
    "modelIdx": 0, "timestamp": ts, "done": True
})

print(f"Success! View at: {API}/c/{chat_id}")
```

## Required Fields

### User Message
```python
{
  "id": str(uuid.uuid4()),           # UUID v4
  "parentId": None,                   # or previous msg ID
  "childrenIds": [],                  # or [next_msg_id]
  "role": "user",
  "content": "message text",
  "timestamp": int(time.time()),      # Unix epoch seconds
  "models": ["recode-cardio-openai"]
}
```

### Assistant Message
```python
{
  "id": str(uuid.uuid4()),           # UUID v4
  "parentId": user_msg_id,           # Required!
  "childrenIds": [],
  "role": "assistant",
  "content": extracted_content,       # From API response!
  "model": "recode-cardio-openai",
  "modelName": "Cardiology",
  "modelIdx": 0,
  "timestamp": int(time.time()),
  "done": True
}
```

## Common Mistakes ❌

| Mistake | Fix |
|---------|-----|
| `"content": "..."}` only | Include all required fields |
| Using `"msg123"` as ID | Use UUID v4: `str(uuid.uuid4())` |
| Not extracting assistant content | `content = resp["choices"][0]["message"]["content"]` |
| Not linking messages | User's `childrenIds: [asst_id]`, Asst's `parentId: user_id` |
| Timestamp in milliseconds | Use seconds: `int(time.time())` not `time.time() * 1000` |

## Verification

```python
# Get chat
chat = requests.get(f"{API}/api/v1/chats/{chat_id}", headers=headers).json()
msgs = chat["chat"]["history"]["messages"]

# Verify
assert msgs[user_id]["role"] == "user"
assert msgs[asst_id]["role"] == "assistant"
assert msgs[asst_id]["content"]  # Must have content!
assert msgs[user_id]["childrenIds"] == [asst_id]
assert msgs[asst_id]["parentId"] == user_id
print("✓ Structure correct!")
```

## Test Scripts

```bash
# Bash
./test_api_chat_persistence.sh

# Python
python3 test_api_chat_persistence.py
```

## Multi-Turn Pattern

```python
parent_id = None  # Start
for question in questions:
    user_id = str(uuid.uuid4())
    asst_id = str(uuid.uuid4())
    
    # Store user msg
    store_message(user_id, parent_id, [asst_id], "user", question)
    
    # Get response
    content = get_completion(question)
    
    # Store assistant msg
    store_message(asst_id, user_id, [], "assistant", content)
    
    parent_id = asst_id  # Next turn
```

## Critical Steps

1. ✅ Generate proper UUIDs
2. ✅ Store complete user message
3. ✅ Call completions endpoint
4. ✅ **Extract content from response**
5. ✅ Update user message with assistant link
6. ✅ **Store complete assistant message with extracted content**

## URLs

- Create chat: `POST /api/v1/chats/new`
- Store message: `POST /api/v1/chats/{chat_id}/messages/{msg_id}`
- Get completion: `POST /api/chat/completions`
- Get chat: `GET /api/v1/chats/{chat_id}`

## Message Tree Visual

```
[User Msg]
  ├─ id: user_id
  ├─ parentId: null
  ├─ childrenIds: [asst_id] ←─┐
  └─ role: "user"              │
                               │ Link
[Assistant Msg]                │
  ├─ id: asst_id               │
  ├─ parentId: user_id ────────┘
  ├─ childrenIds: []
  ├─ role: "assistant"
  └─ content: "..." ← Must extract & store!
```

## Full Documentation

See `API_CHAT_SOLUTION_INDEX.md` for complete documentation set.

---

**Remember:** The key is that `/api/chat/completions` returns the content but doesn't save it. You must extract it from the response and save it yourself!