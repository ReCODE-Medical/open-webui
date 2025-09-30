#!/usr/bin/env python3
"""
Test script for proper API chat persistence
This script demonstrates how to create a chat via API that will display correctly in the UI
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "https://chat.recodemedical.com"
BEARER_TOKEN = "sk-76b5db54dbbe40eb86a2880bf28c070c"
MODEL_ID = "recode-cardio-openai"
MODEL_NAME = "Cardiology"


class ChatAPIClient:
    """Client for interacting with the chat API"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def create_chat(self, title: str) -> Dict[str, Any]:
        """Create a new chat"""
        response = requests.post(
            f"{self.base_url}/api/v1/chats/new",
            headers=self.headers,
            json={
                "chat": {
                    "title": title,
                    "history": {"messages": {}}
                }
            }
        )
        response.raise_for_status()
        return response.json()
    
    def store_message(self, chat_id: str, message_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Store or update a message in a chat"""
        response = requests.post(
            f"{self.base_url}/api/v1/chats/{chat_id}/messages/{message_id}",
            headers=self.headers,
            json=message
        )
        response.raise_for_status()
        return response.json()
    
    def get_completion(self, chat_id: str, message_id: str, model: str, messages: list) -> Dict[str, Any]:
        """Get a chat completion from the model"""
        response = requests.post(
            f"{self.base_url}/api/chat/completions",
            headers=self.headers,
            json={
                "model": model,
                "chat_id": chat_id,
                "id": message_id,
                "messages": messages
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Get a chat by ID"""
        response = requests.get(
            f"{self.base_url}/api/v1/chats/{chat_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def create_user_message(
    message_id: str,
    content: str,
    timestamp: int,
    models: list[str],
    parent_id: Optional[str] = None,
    children_ids: Optional[list[str]] = None
) -> Dict[str, Any]:
    """Create a properly formatted user message object"""
    return {
        "id": message_id,
        "parentId": parent_id,
        "childrenIds": children_ids or [],
        "role": "user",
        "content": content,
        "timestamp": timestamp,
        "models": models
    }


def create_assistant_message(
    message_id: str,
    content: str,
    parent_id: str,
    model: str,
    model_name: str,
    timestamp: int,
    children_ids: Optional[list[str]] = None
) -> Dict[str, Any]:
    """Create a properly formatted assistant message object"""
    return {
        "id": message_id,
        "parentId": parent_id,
        "childrenIds": children_ids or [],
        "role": "assistant",
        "content": content,
        "model": model,
        "modelName": model_name,
        "modelIdx": 0,
        "timestamp": timestamp,
        "done": True
    }


def test_chat_persistence():
    """Test creating a chat with proper message structure"""
    
    print("=== API Chat Persistence Test ===\n")
    
    client = ChatAPIClient(API_BASE_URL, BEARER_TOKEN)
    
    # STEP 1: Create a new chat
    print("STEP 1: Creating new chat...")
    chat = client.create_chat("API Test Chat (Python)")
    chat_id = chat["id"]
    print(f"✓ Chat created with ID: {chat_id}\n")
    
    # Generate IDs and timestamp
    user_msg_id = str(uuid.uuid4())
    assistant_msg_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    print(f"User Message ID: {user_msg_id}")
    print(f"Assistant Message ID: {assistant_msg_id}")
    print(f"Timestamp: {timestamp}\n")
    
    # STEP 2: Store the user message (initially without children)
    print("STEP 2: Storing complete user message...")
    user_content = "What are the key considerations for coding a cardiac catheterization procedure?"
    
    user_message = create_user_message(
        message_id=user_msg_id,
        content=user_content,
        timestamp=timestamp,
        models=[MODEL_ID],
        parent_id=None,
        children_ids=[]
    )
    
    client.store_message(chat_id, user_msg_id, user_message)
    print("✓ User message stored\n")
    
    # STEP 3: Get assistant response
    print("STEP 3: Getting assistant response...")
    
    completion = client.get_completion(
        chat_id=chat_id,
        message_id=assistant_msg_id,
        model=MODEL_ID,
        messages=[{"role": "user", "content": user_content}]
    )
    
    assistant_content = completion["choices"][0]["message"]["content"]
    print(f"✓ Got assistant response ({len(assistant_content)} chars)\n")
    
    # STEP 4: Update user message with childrenIds
    print("STEP 4: Updating user message with childrenIds...")
    
    user_message["childrenIds"] = [assistant_msg_id]
    client.store_message(chat_id, user_msg_id, user_message)
    print("✓ User message updated with assistant link\n")
    
    # STEP 5: Store the complete assistant message
    print("STEP 5: Storing complete assistant message...")
    
    assistant_message = create_assistant_message(
        message_id=assistant_msg_id,
        content=assistant_content,
        parent_id=user_msg_id,
        model=MODEL_ID,
        model_name=MODEL_NAME,
        timestamp=timestamp,
        children_ids=[]
    )
    
    client.store_message(chat_id, assistant_msg_id, assistant_message)
    print("✓ Assistant message stored\n")
    
    # STEP 6: Verify the chat
    print("STEP 6: Verifying chat structure...")
    
    final_chat = client.get_chat(chat_id)
    history = final_chat["chat"]["history"]
    
    print("Final chat structure:")
    print(json.dumps(history, indent=2))
    print()
    
    # Check if the structure is correct
    user_msg = history["messages"].get(user_msg_id, {})
    assistant_msg = history["messages"].get(assistant_msg_id, {})
    current_id = history.get("currentId")
    
    if (user_msg.get("role") == "user" and 
        assistant_msg.get("role") == "assistant" and 
        current_id == assistant_msg_id):
        print("✓✓✓ SUCCESS! Chat structure is correct and should display in UI")
        print(f"View at: {API_BASE_URL}/c/{chat_id}")
    else:
        print("⚠ Warning: Chat structure may not be complete")
        print(f"User message role: {user_msg.get('role')}")
        print(f"Assistant message role: {assistant_msg.get('role')}")
        print(f"Current ID: {current_id}")
    
    print("\n=== Test Complete ===")
    print(f"Chat ID: {chat_id}")
    print(f"User Message ID: {user_msg_id}")
    print(f"Assistant Message ID: {assistant_msg_id}")
    
    return {
        "chat_id": chat_id,
        "user_msg_id": user_msg_id,
        "assistant_msg_id": assistant_msg_id,
        "success": user_msg.get("role") == "user" and assistant_msg.get("role") == "assistant"
    }


def test_multi_turn_conversation():
    """Test creating a multi-turn conversation"""
    
    print("\n\n=== Multi-Turn Conversation Test ===\n")
    
    client = ChatAPIClient(API_BASE_URL, BEARER_TOKEN)
    
    # Create a new chat
    print("Creating new chat...")
    chat = client.create_chat("Multi-Turn Test (Python)")
    chat_id = chat["id"]
    print(f"✓ Chat created with ID: {chat_id}\n")
    
    # Define the conversation
    turns = [
        {
            "user": "What is atrial fibrillation?",
            "expected_topic": "atrial fibrillation"
        },
        {
            "user": "What are the common treatment options?",
            "expected_topic": "treatment"
        }
    ]
    
    parent_id = None
    timestamp = int(time.time())
    
    for i, turn in enumerate(turns, 1):
        print(f"Turn {i}:")
        
        user_msg_id = str(uuid.uuid4())
        assistant_msg_id = str(uuid.uuid4())
        
        # Store user message
        user_message = create_user_message(
            message_id=user_msg_id,
            content=turn["user"],
            timestamp=timestamp + i,
            models=[MODEL_ID],
            parent_id=parent_id,
            children_ids=[assistant_msg_id]
        )
        client.store_message(chat_id, user_msg_id, user_message)
        print(f"  ✓ User message stored")
        
        # Get assistant response
        # For multi-turn, you'd need to build the full message history
        messages = [{"role": "user", "content": turn["user"]}]
        completion = client.get_completion(
            chat_id=chat_id,
            message_id=assistant_msg_id,
            model=MODEL_ID,
            messages=messages
        )
        assistant_content = completion["choices"][0]["message"]["content"]
        print(f"  ✓ Got assistant response ({len(assistant_content)} chars)")
        
        # Store assistant message
        assistant_message = create_assistant_message(
            message_id=assistant_msg_id,
            content=assistant_content,
            parent_id=user_msg_id,
            model=MODEL_ID,
            model_name=MODEL_NAME,
            timestamp=timestamp + i,
            children_ids=[]
        )
        client.store_message(chat_id, assistant_msg_id, assistant_message)
        print(f"  ✓ Assistant message stored\n")
        
        # Update parent_id for next turn
        parent_id = assistant_msg_id
    
    print("✓✓✓ Multi-turn conversation complete!")
    print(f"View at: {API_BASE_URL}/c/{chat_id}")
    
    return chat_id


if __name__ == "__main__":
    try:
        # Test single-turn conversation
        result = test_chat_persistence()
        
        if result["success"]:
            # Test multi-turn conversation
            test_multi_turn_conversation()
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()