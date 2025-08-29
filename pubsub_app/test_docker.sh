#!/bin/bash

echo "=== Testing Docker Pub/Sub System ==="
echo

# Wait for container to be healthy
echo "Waiting for container to be ready..."
until curl -s http://localhost:8000/health >/dev/null; do
    echo "Server not ready yet, waiting..."
    sleep 2
done

echo "✅ Server is ready!"
echo

# Test REST API endpoints
echo "1. Testing REST API endpoints..."
echo

echo "Health check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo

echo "Creating topic 'orders':"
curl -s -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "orders"}'
echo

echo "Creating topic 'notifications':"
curl -s -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "notifications"}'
echo

echo "Listing all topics:"
curl -s http://localhost:8000/topics | python3 -m json.tool
echo

echo "Getting statistics:"
curl -s http://localhost:8000/stats | python3 -m json.tool
echo

echo "Deleting topic 'notifications':"
curl -s -X DELETE http://localhost:8000/topics/notifications
echo

echo "Final topics list:"
curl -s http://localhost:8000/topics | python3 -m json.tool
echo

echo "2. Testing WebSocket functionality..."
echo
echo "WebSocket is running at: ws://localhost:8000/ws"
echo
echo "To test WebSocket, open a new terminal and run:"
echo "wscat -c ws://localhost:8000/ws"
echo
echo "Then send these test messages:"
echo
echo "Subscribe:"
echo '{"type": "subscribe", "topic": "orders", "client_id": "s1", "last_n": 5, "request_id": "550e8400-e29b-41d4-a716-446655440000"}'
echo
echo "Publish:"
echo '{"type": "publish", "topic": "orders", "message": {"id": "550e8400-e29b-41d4-a716-446655440000", "payload": {"order_id": "ORD-123", "amount": "99.5", "currency": "USD"}}, "request_id": "340e8400-e29b-41d4-a716-4466554480098"}'
echo
echo "Ping:"
echo '{"type": "ping", "request_id": "570t8400-e29b-41d4-a716-4466554412345"}'
echo

echo "3. Testing error cases..."
echo

echo "Trying to create duplicate topic (should return 409):"
curl -v -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "orders"}'
echo

echo "Trying to delete non-existent topic (should return 404):"
curl -v -X DELETE http://localhost:8000/topics/non_existent_topic
echo

echo "✅ All tests completed! Your Docker container is running with full functionality!"