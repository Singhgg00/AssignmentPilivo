from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import pubsub


@csrf_exempt
@require_http_methods(["GET", "POST"])
def topics_list_create(request):
    if request.method == "GET":
        topics = pubsub.list_topics()
        return JsonResponse({'topics': topics})

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            topic_name = data.get('name')

            if not topic_name:
                return JsonResponse({'error': 'Topic name is required'}, status=400)

            success = pubsub.create_topic(topic_name)

            if success:
                return JsonResponse({'status': 'created', 'topic': topic_name}, status=201)
            else:
                return JsonResponse({'error': 'Topic already exists'}, status=409)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def topic_detail(request, name):
    success = pubsub.delete_topic(name)
    if success:
        return JsonResponse({'status': 'deleted', 'topic': name})
    else:
        return JsonResponse({'error': 'Topic not found'}, status=404)


@require_http_methods(["GET"])
def health(request):
    health_data = pubsub.get_health()
    return JsonResponse(health_data)


@require_http_methods(["GET"])
def stats(request):
    stats_data = pubsub.get_stats()
    return JsonResponse({'topics': stats_data})
