#!/bin/bash

# Test script for chat API endpoints
# Usage: ./test_chat_endpoints.sh [base_url] [auth_token]

BASE_URL="${1:-http://localhost:8000}"
API_VERSION="/api/v1"
TOKEN="${2:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNGI3ZTM4OC0xMjE4LTQ5NjAtYjVjYi1iODQ4NzIwZDZiOTMiLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiMzI1ZDMwMTQtMGEzYy00YzMzLWI1MTEtODNlZDdhYWI4OTc5IiwiaWF0IjoxNzg4MDQ3NTUyLCJleHAiOjE3ODgwNDkzNTIsInJvbGUiOiJjYW5kaWRhdGUifQ.Bor9yHyB9rQ2qM9gYsWLNwHoTaA8bPV73Kj9n2MtRdo}"

echo "=============================================================="
echo "TESTING CHAT ENDPOINTS"
echo "=============================================================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Create a conversation
echo "TEST 1: Create a new conversation"
echo "POST $BASE_URL$API_VERSION/chat/conversations"
echo ""
CONV_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Test Chat Conversation"}' \
  "$BASE_URL$API_VERSION/chat/conversations")

echo "Response:"
echo "$CONV_RESPONSE" | jq . 2>/dev/null || echo "$CONV_RESPONSE"
echo ""

CONVERSATION_ID=$(echo "$CONV_RESPONSE" | jq -r '.id' 2>/dev/null)
if [ "$CONVERSATION_ID" = "null" ] || [ -z "$CONVERSATION_ID" ]; then
  echo "❌ Failed to create conversation"
  echo "Unable to extract conversation ID. Exiting."
  exit 1
fi

echo "✓ Conversation created with ID: $CONVERSATION_ID"
echo ""

# Test 2: Send a message
echo "TEST 2: Send a message to the conversation"
echo "POST $BASE_URL$API_VERSION/chat/conversations/$CONVERSATION_ID/messages"
echo ""
MSG_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "content":"Hello! Can you help me with my career?",
    "role":"user",
    "metadata":{"source":"mobile_app"}
  }' \
  "$BASE_URL$API_VERSION/chat/conversations/$CONVERSATION_ID/messages")

echo "Response:"
echo "$MSG_RESPONSE" | jq . 2>/dev/null || echo "$MSG_RESPONSE"
echo ""

MESSAGE_ID=$(echo "$MSG_RESPONSE" | jq -r '.id' 2>/dev/null)
if [ "$MESSAGE_ID" != "null" ] && [ -n "$MESSAGE_ID" ]; then
  echo "✓ Message sent with ID: $MESSAGE_ID"
else
  echo "⚠ Message response received but may have issues"
fi
echo ""

# Test 3: Send another message
echo "TEST 3: Send an assistant response message"
echo ""
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "content":"I can help! Tell me about your current role and goals.",
    "role":"assistant",
    "metadata":{"source":"backend_api"}
  }' \
  "$BASE_URL$API_VERSION/chat/conversations/$CONVERSATION_ID/messages" | jq . 2>/dev/null
echo ""

# Test 4: Get conversation with all messages
echo "TEST 4: Get conversation with all messages"
echo "GET $BASE_URL$API_VERSION/chat/conversations/$CONVERSATION_ID"
echo ""
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL$API_VERSION/chat/conversations/$CONVERSATION_ID" | jq . 2>/dev/null
echo ""

# Test 5: List all conversations
echo "TEST 5: List all conversations"
echo "GET $BASE_URL$API_VERSION/chat/conversations"
echo ""
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL$API_VERSION/chat/conversations?limit=10" | jq . 2>/dev/null
echo ""

# Test 6: List messages
echo "TEST 6: List messages (paginated)"
echo "GET $BASE_URL$API_VERSION/chat/messages"
echo ""
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL$API_VERSION/chat/messages?page=1&limit=10" | jq . 2>/dev/null
echo ""

# Test 7: List messages for specific conversation
echo "TEST 7: List messages for specific conversation"
echo "GET $BASE_URL$API_VERSION/chat/messages?conversation_id=$CONVERSATION_ID"
echo ""
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL$API_VERSION/chat/messages?conversation_id=$CONVERSATION_ID" | jq . 2>/dev/null
echo ""

# Test 8: Test unauthorized access (no token)
echo "TEST 8: Test unauthorized access (no auth token)"
echo "GET $BASE_URL$API_VERSION/chat/conversations (no auth)"
echo ""
curl -s -X GET \
  "$BASE_URL$API_VERSION/chat/conversations" | jq . 2>/dev/null
echo ""

echo "=============================================================="
echo "CHAT ENDPOINTS TEST COMPLETE"
echo "=============================================================="
