# Django Pub/Sub System

A simplified in-memory Pub/Sub system built with Django and Django Channels.

## Features

- WebSocket endpoint (`/ws`) for publish/subscribe operations
- REST API for topic management and observability
- In-memory storage (no persistence across restarts)
- Concurrency-safe implementation
- Message history with replay support (`last_n`)
- Bounded message queues (100 messages per topic)

## Setup

1. Build and run with Docker:
```bash
docker-compose up --build

Or Locally:
pip install -r requirements.txt
python manage.py runserver

Feature Testing:
For Testing the Complete Feature Please use this script.:

 chmod +x test_docker.sh
./test_docker.sh

For Manual Testing:
1. REST API Endpoints

curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "orders"}'

List All Topics
curl http://localhost:8000/topics

Delete a Topic
curl -X DELETE http://localhost:8000/topics/orders

Health Check
curl http://localhost:8000/health

Get Statistics
curl http://localhost:8000/stats


2. WebSocket Testing with wscat
npm install -g wscat
wscat -c ws://localhost:8000/ws

Subscribe to a Topic
{"type": "subscribe", "topic": "orders", "client_id": "s1", "last_n": 5, "request_id": "550e8400-e29b-41d4-a716-446655440000"}

Unsubscribe from a Topic
{"type": "unsubscribe", "topic": "orders", "client_id": "s1", "request_id": "340e8400-e29b-41d4-a716-4466554480098"}

Publish a Message
{"type": "publish", "topic": "orders", "message": {"id": "550e8400-e29b-41d4-a716-446655440000", "payload": {"order_id": "ORD-123", "amount": "99.5", "currency": "USD"}}, "request_id": "340e8400-e29b-41d4-a716-4466554480098"}

Send Ping
{"type": "ping", "request_id": "570t8400-e29b-41d4-a716-4466554412345"}


