import logging
import uuid
import redis
import json
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from sorter.schemas.itinerirary_schemas import SortResponse, SortRequest, SortResponseUnion
from sorter.api.v1.endpoints.sort_itineriraries import sort_cheapest, sort_fastest, sort_best
from sorter.api.v1.tasks import sort_task

# Cache
# TODO: Replace with a connection to a real database
redis_client = redis.Redis(host="localhost", port=6379, db=0)
# Cace here is used when user navigates on a result, so we can store the result for a while
CACHE_TTL = 1800  # 30 minutes

# Logging
# Set up Logging, Adapt to log to file or ...
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Itinerary Sorting API",
    description="An API to sort itineraries based on price, duration, or a combination of both",
    version="1.0.0",
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post(
    "/sort_itineraries",
    response_model=SortResponseUnion,
    description=(
        "Sort itineraries based on specified criteria. If `schedule_task` parameter is set to `true`, "
        "the request is handled asynchronously, and a `task_url` is returned. "
        "Use the `task_url` to check back for the sorted results once ready."
    ),
)
@app.get(
    "/sort_itineraries",
    response_model=SortResponse,
    include_in_schema=False,
)
async def sort_itineraries(
    http_request: Request,
    request: SortRequest | None = None,
    schedule_task: bool = Query(
        False, description="If true, schedules the task for background processing and returns a task URL."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    cache_key: str | None = None
):
    if http_request.method == "POST" and not cache_key and not request:
        raise HTTPException(status_code=400, detail="Request body required for initial sorting")

    if http_request.method == "POST" and schedule_task:
        if request.sorting_type not in ["cheapest", "fastest", "best"]:
            raise ValueError("Invalid sorting_type")
        task_id = str(uuid.uuid4())
        sort_task.send(task_id, request.dict())
        task_url = str(http_request.url_for("get_sorting_results", task_id=task_id))
        return {"task_url": task_url}

    if cache_key:
        cached_data = redis_client.get(cache_key)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Cache not found or expired")

        sorted_itineraries = json.loads(cached_data)
    else:
        try:
            if request.sorting_type == "cheapest":
                response = await sort_cheapest(request)
            elif request.sorting_type == "fastest":
                response = await sort_fastest(request)
            elif request.sorting_type == "best":
                response = await sort_best(request)
            else:
                raise HTTPException(status_code=400, detail="Invalid sorting_type provided")
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred. {e.args}")

        sorted_itineraries = response["sorted_itineraries"]

        cache_key = str(uuid.uuid4())
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(sorted_itineraries))

    total_itineraries = len(sorted_itineraries)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_itineraries = sorted_itineraries[start:end]

    base_url = str(http_request.url_for("sort_itineraries"))
    next_url = f"{base_url}?cache_key={cache_key}&page={page + 1}&page_size={page_size}" if end < total_itineraries else None
    previous_url = f"{base_url}?cache_key={cache_key}&page={page - 1}&page_size={page_size}" if start > 0 else None

    paginated_response = SortResponse(
        sorting_type=request.sorting_type if request else "cached",
        page=page,
        page_size=page_size,
        total=total_itineraries,
        next=next_url,
        previous=previous_url,
        sorted_itineraries=paginated_itineraries,
    )
    return paginated_response


@app.get("/sort_itineraries/{task_id}", response_model=SortResponse)
async def get_sorting_results(
    http_request: Request,
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    cached_data = redis_client.get(task_id)
    if not cached_data:
        raise HTTPException(status_code=404, detail="Result not found or still processing ...")

    sorted_itineraries = json.loads(cached_data)
    cache_key = str(uuid.uuid4())
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(sorted_itineraries))

    total_itineraries = len(sorted_itineraries)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_itineraries = sorted_itineraries[start:end]

    base_url = str(http_request.url_for("sort_itineraries"))
    next_url = f"{base_url}?cache_key={cache_key}&page={page + 1}&page_size={page_size}" if end < total_itineraries else None
    previous_url = f"{base_url}?cache_key={cache_key}&page={page - 1}&page_size={page_size}" if start > 0 else None

    paginated_response = SortResponse(
        sorting_type="cached",
        page=page,
        page_size=page_size,
        total=total_itineraries,
        next=next_url,
        previous=previous_url,
        sorted_itineraries=paginated_itineraries,
    )
    return paginated_response
