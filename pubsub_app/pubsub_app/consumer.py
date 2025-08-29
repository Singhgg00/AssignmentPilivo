import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import pubsub
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from datetime import datetime


class PubSubConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.client_id = str(uuid.uuid4())

    async def disconnect(self, close_code):
        # Clean up subscriptions
        await sync_to_async(self._cleanup_subscriptions)()

    def _cleanup_subscriptions(self):
        if hasattr(self, 'client_id') and self.client_id in pubsub.subscriptions:
            for topic in list(pubsub.subscriptions[self.client_id]):
                pubsub.unsubscribe(self.client_id, topic)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'subscribe':
                await self.handle_subscribe(data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscribe(data)
            elif message_type == 'publish':
                await self.handle_publish(data)
            elif message_type == 'ping':
                await self.handle_ping(data)
            else:
                await self.send_error(data.get('request_id'), 'BAD_REQUEST', 'Invalid message type')

        except json.JSONDecodeError:
            await self.send_error(None, 'BAD_REQUEST', 'Invalid JSON')
        except Exception as e:
            await self.send_error(None, 'INTERNAL', str(e))

    async def handle_subscribe(self, data):
        topic = data.get('topic')
        client_id = data.get('client_id')
        last_n = data.get('last_n', 0)
        request_id = data.get('request_id')

        if not topic or not client_id:
            await self.send_error(request_id, 'BAD_REQUEST', 'Missing required fields: topic or client_id')
            return

        self.client_id = client_id

        success, error = await sync_to_async(pubsub.subscribe)(client_id, topic, last_n)

        if success:
            # Add client to group for this topic
            channel_layer = get_channel_layer()
            await channel_layer.group_add(f"client_{client_id}", self.channel_name)

            await self.send_ack(request_id, topic, 'subscribed')
        else:
            await self.send_error(request_id, error, f'Failed to subscribe to topic {topic}')

    async def handle_unsubscribe(self, data):
        topic = data.get('topic')
        client_id = data.get('client_id')
        request_id = data.get('request_id')

        if not topic or not client_id:
            await self.send_error(request_id, 'BAD_REQUEST', 'Missing required fields: topic or client_id')
            return

        success = await sync_to_async(pubsub.unsubscribe)(client_id, topic)

        if success:
            await self.send_ack(request_id, topic, 'unsubscribed')
        else:
            await self.send_error(request_id, 'TOPIC_NOT_FOUND', f'Topic {topic} not found')

    async def handle_publish(self, data):
        topic = data.get('topic')
        message = data.get('message')
        request_id = data.get('request_id')

        if not topic or not message:
            await self.send_error(request_id, 'BAD_REQUEST', 'Missing required fields: topic or message')
            return

        success, error = await sync_to_async(pubsub.publish)(topic, message)

        if success:
            await self.send_ack(request_id, topic, 'published')
        else:
            await self.send_error(request_id, error, f'Failed to publish to topic {topic}')

    async def handle_ping(self, data):
        request_id = data.get('request_id')
        await self.send(json.dumps({
            'type': 'pong',
            'request_id': request_id,
            'ts': datetime.utcnow().isoformat() + 'Z'
        }))

    async def send_ack(self, request_id, topic, status):
        await self.send(json.dumps({
            'type': 'ack',
            'request_id': request_id,
            'topic': topic,
            'status': status,
            'ts': datetime.utcnow().isoformat() + 'Z'
        }))

    async def send_error(self, request_id, code, message):
        await self.send(json.dumps({
            'type': 'error',
            'request_id': request_id,
            'error': {
                'code': code,
                'message': message
            },
            'ts': datetime.utcnow().isoformat() + 'Z'
        }))

    async def event_message(self, event):
        await self.send(json.dumps(event['message']))

    async def info_message(self, event):
        await self.send(json.dumps(event['message']))