import dramatiq
import redis
import json
from dramatiq.brokers.redis import RedisBroker
from asgiref.sync import async_to_sync

from sorter.api.v1.endpoints.sort_itineriraries import sort_cheapest, sort_fastest, sort_best
from sorter.schemas.itinerirary_schemas import SortRequest

# TODO: Replace with a connection to a real database and adjust db and ttl
redis_client = redis.Redis(host="localhost", port=6379, db=0)
CACHE_TTL = 1800  # 30 minutes

broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(broker)


@dramatiq.actor
def sort_task(task_id: str, request_data: dict):
    request = SortRequest(**request_data)

    if request.sorting_type == "cheapest":
        response = async_to_sync(sort_cheapest)(request)
    elif request.sorting_type == "fastest":
        response = async_to_sync(sort_fastest)(request)
    elif request.sorting_type == "best":
        response = async_to_sync(sort_best)(request)
    else:
        raise ValueError("Invalid sorting_type")

    sorted_itineraries = response["sorted_itineraries"]
    redis_client.setex(task_id, CACHE_TTL, json.dumps(sorted_itineraries))
