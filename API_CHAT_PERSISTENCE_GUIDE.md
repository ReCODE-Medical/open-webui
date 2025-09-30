# API Chat Persistence Guide

## Problem Summary

When using the API to create and persist chats, the messages are not displayed correctly in the UI. The chat title appears in the history, but the chat cannot be opened successfully.

## Root Cause

The API currently stores incomplete message objects. Comparing API-created vs UI-created chats reveals missing critical fields:

### What's Missing in API-Created Messages

1. **User Message Missing Fields:**
   - `id` - unique identifier for the message
   - `parentId` - reference to parent message (null for first message)
   - `childrenIds` - array of child message IDs
   - `role` - message role ("user")
   - `timestamp` - when the message was created
   - `models` - array of model IDs used

2. **Assistant Message Missing Fields:**
   - `id` - unique identifier for the message
   - `parentId` - reference to parent message
   - `childrenIds` - array of child message IDs (empty array if no children)
   - `role` - message role ("assistant")
   - `content` - the actual response content
   - `model` - model ID used (stored, but content is missing)
   - `modelName` - human-readable model name
   - `modelIdx` - index of the model (usually 0)
   - `timestamp` - when the message was created
   - `done` - boolean indicating completion
   - Other optional fields: `statusHistory`, `lastSentence`, `followUps`

### Current API Behavior

**STEP 2: Storing user message**
```json
{
  "jhlu432h13pwqh": {
    "content": "This is my first message via API"
  }
}
```

**STEP 3: After chat completion**
```json
{
  "jhlu432h13pwqh": {
    "content": "This is my first message via API"
  },
  "zhealth-asff89799ahshfjs": {
    "model": "recode-cardio-openai"
  }
}
```

### Expected UI Format

**Complete Message Structure:**
```json
{
  "messages": {
    "e474b5bc-678e-4765-ade7-750bc1d8098b": {
      "id": "e474b5bc-678e-4765-ade7-750bc1d8098b",
      "parentId": null,
      "childrenIds": ["50c37152-2a88-496b-a5f4-289efc76f43e"],
      "role": "user",
      "content": "Provide a hypothetical scenario for supraventricular tachycardia.",
      "timestamp": 1759204779,
      "models": ["recode-cardio-openai"]
    },
    "50c37152-2a88-496b-a5f4-289efc76f43e": {
      "parentId": "e474b5bc-678e-4765-ade7-750bc1d8098b",
      "id": "50c37152-2a88-496b-a5f4-289efc76f43e",
      "childrenIds": [],
      "role": "assistant",
      "content": "Here's a hypothetical scenario...",
      "model": "recode-cardio-openai",
      "modelName": "Cardiology",
      "modelIdx": 0,
      "timestamp": 1759204779,
      "done": true
    }
  },
  "currentId": "50c37152-2a88-496b-a5f4-289efc76f43e"
}
```

## Solution

You need to manually construct complete message objects when using the API endpoints. Here's the corrected workflow:

### STEP 1: Create a new chat (same as before)

```bash
curl -X POST "https://chat.recodemedical.com/api/v1/chats/new" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-76b5db54dbbe40eb86a2880bf28c070c" \
  -d '{
    "chat": {
      "title": "Getting it right this time.",
      "history": { "messages": {} }
    }
  }'
```

### STEP 2: Store the COMPLETE user message

```bash
USER_MSG_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"  # Generate proper UUID
TIMESTAMP=$(date +%s)

curl -X POST "https://chat.recodemedical.com/api/v1/chats/69cfc82e-7ad8-4153-99c1-6d02c047d869/messages/${USER_MSG_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-76b5db54dbbe40eb86a2880bf28c070c" \
  -d "{
    \"id\": \"${USER_MSG_ID}\",
    \"parentId\": null,
    \"childrenIds\": [],
    \"role\": \"user\",
    \"content\": \"This is my first message via API\",
    \"timestamp\": ${TIMESTAMP},
    \"models\": [\"recode-cardio-openai\"]
  }"
```

### STEP 3: Get the assistant response

```bash
ASSISTANT_MSG_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"

RESPONSE=$(curl -X POST "https://chat.recodemedical.com/api/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-76b5db54dbbe40eb86a2880bf28c070c" \
  -d "{
    \"model\": \"recode-cardio-openai\",
    \"chat_id\": \"69cfc82e-7ad8-4153-99c1-6d02c047d869\",
    \"id\": \"${ASSISTANT_MSG_ID}\",
    \"messages\": [
      { \"role\": \"user\", \"content\": \"This is my first message via API\" }
    ]
  }")

# Extract the assistant's response content from the JSON
ASSISTANT_CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
```

### STEP 4: Update user message with childrenIds

```bash
curl -X POST "https://chat.recodemedical.com/api/v1/chats/69cfc82e-7ad8-4153-99c1-6d02c047d869/messages/${USER_MSG_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-76b5db54dbbe40eb86a2880bf28c070c" \
  -d "{
    \"id\": \"${USER_MSG_ID}\",
    \"parentId\": null,
    \"childrenIds\": [\"${ASSISTANT_MSG_ID}\"],
    \"role\": \"user\",
    \"content\": \"This is my first message via API\",
    \"timestamp\": ${TIMESTAMP},
    \"models\": [\"recode-cardio-openai\"]
  }"
```

### STEP 5: Store the COMPLETE assistant message

```bash
curl -X POST "https://chat.recodemedical.com/api/v1/chats/69cfc82e-7ad8-4153-99c1-6d02c047d869/messages/${ASSISTANT_MSG_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-76b5db54dbbe40eb86a2880bf28c070c" \
  -d "{
    \"id\": \"${ASSISTANT_MSG_ID}\",
    \"parentId\": \"${USER_MSG_ID}\",
    \"childrenIds\": [],
    \"role\": \"assistant\",
    \"content\": $(echo "$ASSISTANT_CONTENT" | jq -Rs .),
    \"model\": \"recode-cardio-openai\",
    \"modelName\": \"Cardiology\",
    \"modelIdx\": 0,
    \"timestamp\": ${TIMESTAMP},
    \"done\": true
  }"
```

## Key Points

1. **Use proper UUIDs**: Generate valid UUIDs (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) instead of random strings
2. **Include all required fields**: Every message needs `id`, `parentId`, `childrenIds`, `role`, `content`, `timestamp`
3. **Link messages properly**: User messages should have the assistant message ID in `childrenIds`, assistant messages should have the user message ID in `parentId`
4. **Store the assistant response content**: The `/api/chat/completions` endpoint doesn't automatically save the response content - you must extract it and save it separately
5. **Use consistent timestamps**: Both user and assistant messages in the same turn typically share the same timestamp

## Alternative: Use the Update Chat Endpoint

Instead of using individual message endpoints, you can update the entire chat history at once:

```bash
curl -X POST "https://chat.recodemedical.com/api/v1/chats/69cfc82e-7ad8-4153-99c1-6d02c047d869" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-76b5db54dbbe40eb86a2880bf28c070c" \
  -d "{
    \"chat\": {
      \"title\": \"Getting it right this time.\",
      \"models\": [\"recode-cardio-openai\"],
      \"history\": {
        \"messages\": {
          \"${USER_MSG_ID}\": {
            \"id\": \"${USER_MSG_ID}\",
            \"parentId\": null,
            \"childrenIds\": [\"${ASSISTANT_MSG_ID}\"],
            \"role\": \"user\",
            \"content\": \"This is my first message via API\",
            \"timestamp\": ${TIMESTAMP},
            \"models\": [\"recode-cardio-openai\"]
          },
          \"${ASSISTANT_MSG_ID}\": {
            \"id\": \"${ASSISTANT_MSG_ID}\",
            \"parentId\": \"${USER_MSG_ID}\",
            \"childrenIds\": [],
            \"role\": \"assistant\",
            \"content\": $(echo "$ASSISTANT_CONTENT" | jq -Rs .),
            \"model\": \"recode-cardio-openai\",
            \"modelName\": \"Cardiology\",
            \"modelIdx\": 0,
            \"timestamp\": ${TIMESTAMP},
            \"done\": true
          }
        },
        \"currentId\": \"${ASSISTANT_MSG_ID}\"
      }
    }
  }"
```

## Backend Code Location

The issue stems from how the `/api/chat/completions` endpoint handles message persistence:

- **Chat completion endpoint**: `/workspace/backend/open_webui/main.py:1372-1512`
- **Message upsert logic**: `/workspace/backend/open_webui/models/chats.py:312-337`
- **UI message structure**: `/workspace/src/lib/utils/index.ts:191-222` (see `convertMessagesToHistory`)

The `/api/chat/completions` endpoint only stores minimal fields (`model` field) for the assistant message, not the complete message structure that the UI expects.

## Recommended Backend Fix

The proper fix would be to modify the `/api/chat/completions` endpoint to store complete message objects automatically. The endpoint should:

1. Accept the user message ID as a parameter
2. Create a properly structured user message with all required fields
3. After getting the assistant response, create a properly structured assistant message
4. Link the messages together (parentId/childrenIds)
5. Return both message IDs in the response

This would make the API experience match the UI experience.