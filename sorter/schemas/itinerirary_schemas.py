from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Literal, Optional, Union


class Price(BaseModel):
    amount: float
    currency: str


class Itinerary(BaseModel):
    id: str
    duration_minutes: int
    price: Price


class SortRequest(BaseModel):
    """
    Model representing the request to sort itineraries based on a specified type,
    with optional weighting for price and duration in the "best" sort.
    """
    sorting_type: Literal["cheapest", "fastest", "best"]
    price_weight: Optional[float] = 0.5
    duration_weight: Optional[float] = 0.5
    itineraries: List[Itinerary] = Field(
        ...,
        example=[
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
            },
            {
                "id": "itinerary_3",
                "duration_minutes": 150,
                "price": {
                    "amount": 80.0,
                    "currency": "USD"
                }
            }
        ]
    )

    @field_validator("duration_weight", mode="before")
    def check_weights_sum(cls, duration_weight, values):
        price_weight = values.data.get("price_weight", 0.5)
        if price_weight + duration_weight != 1:
            raise ValueError("price_weight and duration_weight must sum up to 1")
        return duration_weight


class SortResponse(BaseModel):
    """
    Model representing the sorted response of itineraries, providing details
    on the type of sorting used and the list of sorted itineraries.
    """
    sorting_type: str
    page: int
    page_size: int
    total: int
    next: Optional[HttpUrl] = None
    previous: Optional[HttpUrl] = None
    sorted_itineraries: List[Itinerary]


class ScheduledTaskResponse(BaseModel):
    """
    Model for the asynchronous response when a sorting task is scheduled.
    """
    task_url: HttpUrl


SortResponseUnion = Union[SortResponse, ScheduledTaskResponse]
