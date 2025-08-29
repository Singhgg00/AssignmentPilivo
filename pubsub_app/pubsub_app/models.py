import uuid
import time
from datetime import datetime
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from collections import deque
import threading


class InMemoryPubSub:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.topics = {}  # topic_name -> TopicInfo
        self.subscriptions = {}  # client_id -> set(topic_names)
        self.topic_subscribers = {}  # topic_name -> set(client_ids)
        self.message_history = {}  # topic_name -> deque(maxlen=100)
        self.start_time = time.time()

    def create_topic(self, name):
        with self._lock:
            if name in self.topics:
                return False
            self.topics[name] = {
                'created_at': timezone.now(),
                'message_count': 0,
                'subscriber_count': 0
            }
            self.message_history[name] = deque(maxlen=100)
            self.topic_subscribers[name] = set()
            return True

    def delete_topic(self, name):
        with self._lock:
            if name not in self.topics:
                return False

            # Notify all subscribers
            channel_layer = get_channel_layer()
            for client_id in list(self.topic_subscribers.get(name, [])):
                async_to_sync(channel_layer.group_send)(
                    f"client_{client_id}",
                    {
                        'type': 'info_message',
                        'message': {
                            'type': 'info',
                            'topic': name,
                            'msg': 'topic_deleted',
                            'ts': datetime.utcnow().isoformat() + 'Z'
                        }
                    }
                )
                self.unsubscribe(client_id, name)

            del self.topics[name]
            del self.message_history[name]
            del self.topic_subscribers[name]
            return True

    def list_topics(self):
        with self._lock:
            return [
                {
                    'name': name,
                    'subscribers': info['subscriber_count']
                }
                for name, info in self.topics.items()
            ]

    def get_stats(self):
        with self._lock:
            return {
                name: {
                    'messages': info['message_count'],
                    'subscribers': info['subscriber_count']
                }
                for name, info in self.topics.items()
            }

    def get_health(self):
        with self._lock:
            total_subscribers = sum(len(subs) for subs in self.topic_subscribers.values())
            return {
                'uptime_sec': int(time.time() - self.start_time),
                'topics': len(self.topics),
                'subscribers': total_subscribers
            }

    def subscribe(self, client_id, topic_name, last_n=0):
        with self._lock:
            if topic_name not in self.topics:
                return False, "TOPIC_NOT_FOUND"

            if client_id not in self.subscriptions:
                self.subscriptions[client_id] = set()

            if topic_name not in self.subscriptions[client_id]:
                self.subscriptions[client_id].add(topic_name)
                self.topic_subscribers[topic_name].add(client_id)
                self.topics[topic_name]['subscriber_count'] = len(self.topic_subscribers[topic_name])

            # Send historical messages if requested
            if last_n > 0 and topic_name in self.message_history:
                channel_layer = get_channel_layer()
                history = list(self.message_history[topic_name])[-last_n:]
                for msg in history:
                    async_to_sync(channel_layer.group_send)(
                        f"client_{client_id}",
                        {
                            'type': 'event_message',
                            'message': msg
                        }
                    )

            return True, None

    def unsubscribe(self, client_id, topic_name):
        with self._lock:
            if client_id in self.subscriptions and topic_name in self.subscriptions[client_id]:
                self.subscriptions[client_id].remove(topic_name)
                if not self.subscriptions[client_id]:
                    del self.subscriptions[client_id]

            if topic_name in self.topic_subscribers and client_id in self.topic_subscribers[topic_name]:
                self.topic_subscribers[topic_name].remove(client_id)
                self.topics[topic_name]['subscriber_count'] = len(self.topic_subscribers[topic_name])

            return True

    def publish(self, topic_name, message):
        with self._lock:
            if topic_name not in self.topics:
                return False, "TOPIC_NOT_FOUND"

            # Validate message structure
            if 'id' not in message or 'payload' not in message:
                return False, "BAD_REQUEST"

            try:
                uuid.UUID(message['id'])
            except (ValueError, TypeError):
                return False, "BAD_REQUEST"

            # Store message in history
            event_message = {
                'type': 'event',
                'topic': topic_name,
                'message': message,
                'ts': datetime.utcnow().isoformat() + 'Z'
            }

            self.message_history[topic_name].append(event_message)
            self.topics[topic_name]['message_count'] += 1

            # Broadcast to all subscribers
            channel_layer = get_channel_layer()
            for client_id in self.topic_subscribers.get(topic_name, []):
                async_to_sync(channel_layer.group_send)(
                    f"client_{client_id}",
                    {
                        'type': 'event_message',
                        'message': event_message
                    }
                )

            return True, None


# Global instance
pubsub = InMemoryPubSub()