#!/bin/bash

# Test script for proper API chat persistence
# This script demonstrates how to create a chat via API that will display correctly in the UI

set -e

# Configuration
API_BASE_URL="https://chat.recodemedical.com"
BEARER_TOKEN="sk-76b5db54dbbe40eb86a2880bf28c070c"
MODEL_ID="recode-cardio-openai"
MODEL_NAME="Cardiology"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== API Chat Persistence Test ===${NC}\n"

# STEP 1: Create a new chat
echo -e "${YELLOW}STEP 1: Creating new chat...${NC}"
CHAT_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/chats/new" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -d '{
    "chat": {
      "title": "API Test Chat",
      "history": { "messages": {} }
    }
  }')

CHAT_ID=$(echo "$CHAT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Chat created with ID: ${CHAT_ID}${NC}\n"

# Generate UUIDs for messages
USER_MSG_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
ASSISTANT_MSG_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
TIMESTAMP=$(date +%s)

echo -e "User Message ID: ${USER_MSG_ID}"
echo -e "Assistant Message ID: ${ASSISTANT_MSG_ID}"
echo -e "Timestamp: ${TIMESTAMP}\n"

# STEP 2: Store the complete user message
echo -e "${YELLOW}STEP 2: Storing complete user message...${NC}"

USER_MESSAGE_CONTENT="What are the key considerations for coding a cardiac catheterization procedure?"

# First, store the user message with empty childrenIds
curl -s -X POST "${API_BASE_URL}/api/v1/chats/${CHAT_ID}/messages/${USER_MSG_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -d "{
    \"id\": \"${USER_MSG_ID}\",
    \"parentId\": null,
    \"childrenIds\": [],
    \"role\": \"user\",
    \"content\": \"${USER_MESSAGE_CONTENT}\",
    \"timestamp\": ${TIMESTAMP},
    \"models\": [\"${MODEL_ID}\"]
  }" > /dev/null

echo -e "${GREEN}✓ User message stored${NC}\n"

# STEP 3: Get the assistant response
echo -e "${YELLOW}STEP 3: Getting assistant response...${NC}"

COMPLETION_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"chat_id\": \"${CHAT_ID}\",
    \"id\": \"${ASSISTANT_MSG_ID}\",
    \"messages\": [
      { \"role\": \"user\", \"content\": \"${USER_MESSAGE_CONTENT}\" }
    ]
  }")

# Extract the assistant's response content
ASSISTANT_CONTENT=$(echo "$COMPLETION_RESPONSE" | jq -r '.choices[0].message.content')

if [ "$ASSISTANT_CONTENT" == "null" ] || [ -z "$ASSISTANT_CONTENT" ]; then
  echo -e "${YELLOW}⚠ Warning: No content in assistant response${NC}"
  echo "Response: $COMPLETION_RESPONSE"
  ASSISTANT_CONTENT="Error: No response content"
fi

echo -e "${GREEN}✓ Got assistant response (${#ASSISTANT_CONTENT} chars)${NC}\n"

# STEP 4: Update user message with childrenIds
echo -e "${YELLOW}STEP 4: Updating user message with childrenIds...${NC}"

curl -s -X POST "${API_BASE_URL}/api/v1/chats/${CHAT_ID}/messages/${USER_MSG_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -d "{
    \"id\": \"${USER_MSG_ID}\",
    \"parentId\": null,
    \"childrenIds\": [\"${ASSISTANT_MSG_ID}\"],
    \"role\": \"user\",
    \"content\": \"${USER_MESSAGE_CONTENT}\",
    \"timestamp\": ${TIMESTAMP},
    \"models\": [\"${MODEL_ID}\"]
  }" > /dev/null

echo -e "${GREEN}✓ User message updated with assistant link${NC}\n"

# STEP 5: Store the complete assistant message
echo -e "${YELLOW}STEP 5: Storing complete assistant message...${NC}"

# Escape the assistant content for JSON
ASSISTANT_CONTENT_JSON=$(echo "$ASSISTANT_CONTENT" | jq -Rs .)

curl -s -X POST "${API_BASE_URL}/api/v1/chats/${CHAT_ID}/messages/${ASSISTANT_MSG_ID}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -d "{
    \"id\": \"${ASSISTANT_MSG_ID}\",
    \"parentId\": \"${USER_MSG_ID}\",
    \"childrenIds\": [],
    \"role\": \"assistant\",
    \"content\": ${ASSISTANT_CONTENT_JSON},
    \"model\": \"${MODEL_ID}\",
    \"modelName\": \"${MODEL_NAME}\",
    \"modelIdx\": 0,
    \"timestamp\": ${TIMESTAMP},
    \"done\": true
  }" > /dev/null

echo -e "${GREEN}✓ Assistant message stored${NC}\n"

# STEP 6: Verify the chat
echo -e "${YELLOW}STEP 6: Verifying chat structure...${NC}"

FINAL_CHAT=$(curl -s -X GET "${API_BASE_URL}/api/v1/chats/${CHAT_ID}" \
  -H "Authorization: Bearer ${BEARER_TOKEN}")

echo "Final chat structure:"
echo "$FINAL_CHAT" | jq '.chat.history'

# Check if the structure is correct
USER_MSG_CHECK=$(echo "$FINAL_CHAT" | jq -r ".chat.history.messages.\"${USER_MSG_ID}\".role")
ASSISTANT_MSG_CHECK=$(echo "$FINAL_CHAT" | jq -r ".chat.history.messages.\"${ASSISTANT_MSG_ID}\".role")
CURRENT_ID_CHECK=$(echo "$FINAL_CHAT" | jq -r ".chat.history.currentId")

echo ""
if [ "$USER_MSG_CHECK" == "user" ] && [ "$ASSISTANT_MSG_CHECK" == "assistant" ] && [ "$CURRENT_ID_CHECK" == "$ASSISTANT_MSG_ID" ]; then
  echo -e "${GREEN}✓✓✓ SUCCESS! Chat structure is correct and should display in UI${NC}"
  echo -e "${GREEN}View at: ${API_BASE_URL}/c/${CHAT_ID}${NC}"
else
  echo -e "${YELLOW}⚠ Warning: Chat structure may not be complete${NC}"
  echo "User message role: $USER_MSG_CHECK"
  echo "Assistant message role: $ASSISTANT_MSG_CHECK"
  echo "Current ID: $CURRENT_ID_CHECK"
fi

echo ""
echo -e "${BLUE}=== Test Complete ===${NC}"
echo "Chat ID: ${CHAT_ID}"
echo "User Message ID: ${USER_MSG_ID}"
echo "Assistant Message ID: ${ASSISTANT_MSG_ID}"