# Message Structure Visual Guide

## Current Broken API Behavior vs Expected Structure

### ❌ What the API Currently Saves (Incomplete)

```
Step 2 - Store user message with minimal data:
┌─────────────────────────────────────┐
│ Message ID: "jhlu432h13pwqh"       │
│ {                                   │
│   "content": "My message"           │
│ }                                   │
│                                     │
│ Missing: id, parentId, childrenIds, │
│          role, timestamp, models    │
└─────────────────────────────────────┘

Step 3 - Completions endpoint saves even less:
┌─────────────────────────────────────┐
│ Message ID: "zhealth-asff8979..."  │
│ {                                   │
│   "model": "recode-cardio-openai"   │
│ }                                   │
│                                     │
│ Missing: id, parentId, childrenIds, │
│          role, content (!),         │
│          timestamp, modelName, done │
└─────────────────────────────────────┘

Result: UI cannot render the chat because:
- No role field → doesn't know if user/assistant
- No content in assistant → nothing to display
- No parentId/childrenIds → can't build message tree
- No timestamp → can't show message time
```

### ✅ What the UI Expects (Complete Structure)

```
User Message:
┌────────────────────────────────────────────────────┐
│ Message ID: "e474b5bc-678e-4765-ade7-750bc1d8098b" │
├────────────────────────────────────────────────────┤
│ {                                                  │
│   "id": "e474b5bc-678e-4765-ade7-750bc1d8098b",   │
│   "parentId": null,                  ← No previous msg│
│   "childrenIds": [                   ← Links to next│
│     "50c37152-2a88-496b-a5f4-289efc76f43e"        │
│   ],                                               │
│   "role": "user",                    ← Required!   │
│   "content": "Provide a hypothetical scenario...", │
│   "timestamp": 1759204779,           ← Unix epoch  │
│   "models": ["recode-cardio-openai"] ← Which models│
│ }                                                  │
└────────────────────────────────────────────────────┘
         │
         │ childrenIds link
         ▼
┌────────────────────────────────────────────────────┐
│ Message ID: "50c37152-2a88-496b-a5f4-289efc76f43e" │
├────────────────────────────────────────────────────┤
│ {                                                  │
│   "id": "50c37152-2a88-496b-a5f4-289efc76f43e",   │
│   "parentId": "e474b5bc-678e...",   ← Links back   │
│   "childrenIds": [],                 ← End of chain│
│   "role": "assistant",               ← Required!   │
│   "content": "Here's a hypothetical scenario...",  │
│   "model": "recode-cardio-openai",                 │
│   "modelName": "Cardiology",         ← Display name│
│   "modelIdx": 0,                     ← Model index │
│   "timestamp": 1759204779,           ← Same time   │
│   "done": true,                      ← Completed   │
│   "statusHistory": [...],            ← Optional    │
│   "followUps": [...]                 ← Optional    │
│ }                                                  │
└────────────────────────────────────────────────────┘
```

## Message Tree Structure

### Single Turn Conversation
```
Chat History
├── messages: {
│   ├── "user-msg-1": {
│   │     id: "user-msg-1"
│   │     parentId: null
│   │     childrenIds: ["asst-msg-1"]
│   │     role: "user"
│   │     content: "Hello"
│   │     ...
│   │   }
│   └── "asst-msg-1": {
│         id: "asst-msg-1"
│         parentId: "user-msg-1"
│         childrenIds: []
│         role: "assistant"
│         content: "Hi there!"
│         ...
│       }
│ }
└── currentId: "asst-msg-1"
```

### Multi-Turn Conversation
```
Chat History
├── messages: {
│   ├── "user-msg-1": {parentId: null, childrenIds: ["asst-msg-1"]}
│   ├── "asst-msg-1": {parentId: "user-msg-1", childrenIds: ["user-msg-2"]}
│   ├── "user-msg-2": {parentId: "asst-msg-1", childrenIds: ["asst-msg-2"]}
│   └── "asst-msg-2": {parentId: "user-msg-2", childrenIds: []}
│ }
└── currentId: "asst-msg-2"

Visual Tree:
  [User 1] ──→ [Assistant 1] ──→ [User 2] ──→ [Assistant 2]
   ↑              ↑                 ↑              ↑
   │              │                 │              │
   │              └─ parentId       └─ parentId    └─ currentId
   └─ parentId: null
```

### Branching Conversation (Multiple Responses)
```
Chat History
├── messages: {
│   ├── "user-msg-1": {parentId: null, childrenIds: ["asst-1a", "asst-1b"]}
│   ├── "asst-1a": {parentId: "user-msg-1", childrenIds: ["user-msg-2"]}
│   ├── "asst-1b": {parentId: "user-msg-1", childrenIds: []}
│   └── "user-msg-2": {parentId: "asst-1a", childrenIds: []}
│ }
└── currentId: "user-msg-2"

Visual Tree:
                    ┌─→ [Assistant 1a] ──→ [User 2]
                    │      (selected)         ↑
  [User 1] ────────┤                          │
                    │                          └─ currentId
                    └─→ [Assistant 1b]
                           (alternative)
```

## Complete Chat Object Structure

```json
{
  "id": "chat-uuid",
  "user_id": "user-uuid",
  "title": "Chat Title",
  "chat": {
    "id": "",                           // Often empty
    "title": "Chat Title",              
    "models": ["recode-cardio-openai"], // Array of model IDs
    "params": {},                       // Model parameters
    "history": {
      "messages": {
        "msg-uuid-1": { /* message object */ },
        "msg-uuid-2": { /* message object */ }
      },
      "currentId": "msg-uuid-2"         // Last active message
    },
    "messages": [ /* optional array format */ ],
    "tags": [],
    "timestamp": 1759204779173,
    "files": []
  },
  "updated_at": 1759204796,
  "created_at": 1759204779,
  "share_id": null,
  "archived": false,
  "pinned": false,
  "meta": {
    "tags": ["cardiology", "electrophysiology"]
  },
  "folder_id": null
}
```

## Data Flow Comparison

### ❌ Current Broken Flow

```
1. User creates chat
   → Chat exists in DB with empty messages

2. User stores message via API
   → POST /api/v1/chats/{id}/messages/{msg_id}
   → Body: {"content": "Hello"}
   → Stored: {"content": "Hello"}  ← Incomplete!

3. User calls completions
   → POST /api/chat/completions
   → Response: {"choices": [{"message": {"content": "Response"}}]}
   → Stored: {"model": "model-id"}  ← Missing content!

4. User tries to view in UI
   → UI loads chat
   → UI tries to parse messages
   → Missing fields cause render failure
   → Chat appears broken ❌
```

### ✅ Correct Flow

```
1. User creates chat
   → Chat exists in DB with empty messages

2. User stores COMPLETE message via API
   → POST /api/v1/chats/{id}/messages/{msg_id}
   → Body: {
       "id": "msg-uuid",
       "parentId": null,
       "childrenIds": [],
       "role": "user",
       "content": "Hello",
       "timestamp": 1234567890,
       "models": ["model-id"]
     }
   → Stored: Complete message object ✓

3. User calls completions AND extracts content
   → POST /api/chat/completions
   → Response: {"choices": [{"message": {"content": "Response"}}]}
   → Extract: content = response["choices"][0]["message"]["content"]

4. User updates user message with link
   → POST /api/v1/chats/{id}/messages/{user_msg_id}
   → Body: {..., "childrenIds": ["asst_msg_id"]}

5. User stores COMPLETE assistant message
   → POST /api/v1/chats/{id}/messages/{asst_msg_id}
   → Body: {
       "id": "asst-uuid",
       "parentId": "user-uuid",
       "childrenIds": [],
       "role": "assistant",
       "content": "Response",  ← From step 3!
       "model": "model-id",
       "modelName": "Model Name",
       "modelIdx": 0,
       "timestamp": 1234567890,
       "done": true
     }
   → Stored: Complete message object ✓

6. User views in UI
   → UI loads chat
   → UI parses complete messages
   → UI renders conversation correctly ✓
```

## Field Descriptions

### Common Fields (User & Assistant)
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique message identifier (UUID v4) | `"e474b5bc-678e-4765-ade7-750bc1d8098b"` |
| `parentId` | string\|null | ID of previous message in thread | `"previous-msg-uuid"` or `null` |
| `childrenIds` | array | IDs of following messages | `["next-msg-uuid"]` or `[]` |
| `role` | string | Message sender type | `"user"` or `"assistant"` |
| `content` | string | The actual message text | `"Hello, how are you?"` |
| `timestamp` | integer | Unix epoch seconds | `1759204779` |

### User Message Specific
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `models` | array | List of model IDs to use | `["recode-cardio-openai"]` |

### Assistant Message Specific
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `model` | string | Model ID that generated response | `"recode-cardio-openai"` |
| `modelName` | string | Human-readable model name | `"Cardiology"` |
| `modelIdx` | integer | Index of model (for multi-model) | `0` |
| `done` | boolean | Whether generation is complete | `true` |
| `statusHistory` | array | Optional status updates during generation | `[{"action": "thinking", "done": true}]` |
| `followUps` | array | Optional suggested follow-up questions | `["What about...", "How does..."]` |
| `lastSentence` | string | Optional last sentence (for streaming) | `"Hope this helps!"` |

## Quick Reference: Required vs Optional Fields

### User Message
```javascript
{
  id: required,           // UUID v4 format
  parentId: required,     // null for first message
  childrenIds: required,  // array, can be empty []
  role: required,         // must be "user"
  content: required,      // the message text
  timestamp: required,    // unix epoch seconds
  models: required        // array of model IDs
}
```

### Assistant Message
```javascript
{
  id: required,           // UUID v4 format
  parentId: required,     // user message UUID
  childrenIds: required,  // array, can be empty []
  role: required,         // must be "assistant"
  content: required,      // the response text
  model: required,        // model ID
  modelName: required,    // human-readable name
  modelIdx: required,     // usually 0
  timestamp: required,    // unix epoch seconds
  done: required,         // true when complete
  
  // Optional but recommended:
  statusHistory: optional,
  followUps: optional,
  lastSentence: optional
}
```

## Common Errors and Fixes

### Error: Chat loads but shows no messages
**Cause:** Missing `role` field
**Fix:** Ensure both user and assistant messages have `"role": "user"` or `"role": "assistant"`

### Error: Messages appear disconnected
**Cause:** Missing or incorrect `parentId`/`childrenIds` links
**Fix:** User message's `childrenIds` must include assistant ID; assistant's `parentId` must match user ID

### Error: Assistant message is blank
**Cause:** Missing `content` field in assistant message
**Fix:** Extract content from completions API response and store it

### Error: "Invalid UUID" or similar
**Cause:** Using random strings instead of proper UUIDs
**Fix:** Use UUID v4 format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (lowercase with hyphens)

### Error: Timestamps appear wrong in UI
**Cause:** Using milliseconds instead of seconds
**Fix:** Use Unix epoch seconds, not milliseconds (e.g., `1759204779`, not `1759204779000`)

## Summary

The key to successful API chat persistence is understanding that:

1. **Messages form a tree structure** using `parentId` and `childrenIds`
2. **All fields are required** - the API doesn't fill in defaults
3. **The completions endpoint doesn't persist the response** - you must extract and store it
4. **UUIDs must be proper v4 format** - not random strings
5. **Messages must be linked bidirectionally** - parent→children and children→parent

Follow the examples in the test scripts and documentation to ensure correct implementation.