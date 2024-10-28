
# Itinerary Sorting API

This FastAPI application provides an API to sort itineraries based on various criteria such as price, duration, or a custom combination of both. The API supports both synchronous and asynchronous processing modes, allowing you to either get results immediately or schedule a background task and check back later.

## Features

- Sort itineraries by:
  - **Cheapest**: Sorts by the lowest price.
  - **Fastest**: Sorts by the shortest duration.
  - **Best**: Sorts based on a combination of price and duration.
- **Pagination** for large lists of itineraries.
- **Caching** results to Redis for efficient retrieval.
- **Dual Processing Modes**:
  - **Synchronous Mode**: Immediate sorting with results returned directly.
  - **Asynchronous Mode**: Schedule sorting in the background and retrieve results via a task URL.

## Requirements

- **Python 3.8+**
- **Redis** (for caching and task queue management)
- **Dramatiq** (for background task processing)

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/al2m4n/itinerary-sorting-api.git
   cd itinerary-sorting-api
   ```

2. **Set up a virtual environment** (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies using poetry** (if you don't have it already use pip install poetry):

   ```bash
   poetry install
   ```

4. **Install and run Redis**:

   - Install Redis ([Redis installation guide](https://redis.io/download)).
   - Start Redis on the default port (6379) by running:

     ```bash
     redis-server
     ```

## Configuration

Make sure Redis is running on `localhost` at port `6379` (default). If needed, you can adjust Redis settings in the `main.py` file by changing the `host` and `port` in the `redis_client` connection.

## Running the Application

### Start FastAPI Server

To run the FastAPI application, use the command (adjust if needed):

```bash
uvicorn sorter.main:app --host 0.0.0.0 --port 8000 --reload --workers 2
```

This will start the server at `http://127.0.0.1:8000`.

### Run Dramatiq Worker

In a separate terminal window, start the Dramatiq worker to process background tasks:

```bash
dramatiq sorter.api.v1.tasks
```

### API Documentation

The API documentation is available at:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Schema: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

## Usage

### 1. Synchronous Mode (Immediate Sorting)

In the synchronous mode, the sorting results are returned directly. This is the default mode if the `schedule_task` parameter is not included or is set to `false`. It is still leveraging async but not fully, use Asynchronous mode for full async.

#### Request

```http
POST /sort_itineraries
Content-Type: application/json
```

#### Example JSON Body
(price_weight and duration_weight are optional, default is 0.5 for both)
```json
{
  "sorting_type": "best",
  "price_weight": 0.5,
  "duration_weight": 0.5,
  "itineraries": [
    {
      "id": "itinerary_1",
      "duration_minutes": 120,
      "price": {
        "amount": 100.0,
        "currency": "EUR"
      }
    },
    {
      "id": "itinerary_2",
      "duration_minutes": 90,
      "price": {
        "amount": 120.0,
        "currency": "EUR"
      }
    }
  ]
}
```

#### Response

A successful response returns sorted itineraries along with pagination information:

```json
{
  "sorting_type": "best",
  "page": 1,
  "page_size": 10,
  "total": 2,
  "next": null,
  "previous": null,
  "sorted_itineraries": [
    {
      "id": "itinerary_1",
      "duration_minutes": 120,
      "price": {
        "amount": 100.0,
        "currency": "EUR"
      }
    },
    {
      "id": "itinerary_2",
      "duration_minutes": 90,
      "price": {
        "amount": 120.0,
        "currency": "EUR"
      }
    }
  ]
}
```

### 2. Asynchronous Mode (Task Scheduling)

If `schedule_task=true` is passed as a query parameter, the API schedules the sorting task to be processed in the background. You will receive a `task_url` to check back later for the results.

#### Request

```http
POST /sort_itineraries?schedule_task=true
Content-Type: application/json
```

#### Response

The response will include a `task_url`, which can be used to check the task’s status and retrieve results once they are ready.

```json
{
  "task_url": "http://127.0.0.1:8000/sort_itineraries/<task_id>"
}
```

#### Check Task Status and Retrieve Results

To retrieve the results once they are ready, make a `GET` request to the `task_url` provided in the initial response.

```http
GET /sort_itineraries/<task_id>
```

If the task is still processing, you will receive a `404` response. Once completed, the response will include the sorted itineraries and pagination data.

## Testing

You can use **Postman** or **cURL** to interact with the API. For example, to test asynchronous sorting:

```bash
curl -X POST "http://127.0.0.1:8000/sort_itineraries?schedule_task=true" -H "Content-Type: application/json" -d '{
 "sorting_type": "cheapest",
 "itineraries": [
    {
      "id": "itinerary_1",
      "duration_minutes": 120,
      "price": {
        "amount": 100.0,
        "currency": "EUR"
      }
    },
    {
      "id": "itinerary_2",
      "duration_minutes": 90,
      "price": {
        "amount": 120.0,
        "currency": "USD"
      }
    }
 ]
}'
```

## Development

To make modifications, follow these guidelines:

- **`main.py`**: Main application entry point and route definitions.
- **`tasks.py`**: Background task definitions for asynchronous processing with Dramatiq.
- **`schemas/itinerary_schemas.py`**: Pydantic models for request validation and response formatting.
- **`api/v1/endpoints/sort_itineriraries.py`**: Sorting logic and caching implementation.
- **`tests/`**: Unit tests for the application.
- **`poetry.lock`** and **`pyproject.toml`**: Dependency management with Poetry.


## Possible Improvements

- Redis caching is used for storing the result for tasks, and also used for navigating through the paginated results. This can be improved by creating a dynamic key based on the data of the itineraries and store it so if the same request is posted again from different user it should return the cached data if not expired.
- Used Dramatiq for background task processing, this can be improved by using a more robust task queue like Celery.
- Use better currency conversion API to convert the currency of the itineraries to a common currency before sorting.
- Add CI file for github actions to run tests on each pull request and deploy after the merge.
- Add fetching json data from file or cloud storage.
- And much more ...
