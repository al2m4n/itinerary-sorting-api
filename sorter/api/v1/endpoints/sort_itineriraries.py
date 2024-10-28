import pandas as pd
import numpy as np

from sorter.schemas.itinerirary_schemas import SortRequest
from sorter.api.utils import convert_prices_async, add_score_to_itineraries


async def sort_cheapest(request: SortRequest):
    itineraries = request.itineraries
    sorting_type = request.sorting_type

    data = [
        {
            "id": itinerary.id,
            "duration_minutes": itinerary.duration_minutes,
            "price_amount": float(itinerary.price.amount),
            "price_currency": itinerary.price.currency
        }
        for itinerary in itineraries
    ]
    itineraries_df = pd.DataFrame(data)

    await convert_prices_async(itineraries_df)

    sorted_indices = np.argsort(itineraries_df["price_eur"].values)
    sorted_df = itineraries_df.iloc[sorted_indices].reset_index(drop=True)
    sorted_itineraries = sorted_df.drop(columns="price_eur").to_dict(orient="records")

    response = {
        "sorting_type": sorting_type,
        "sorted_itineraries": [
            {
                "id": item["id"],
                "duration_minutes": item["duration_minutes"],
                "price": {
                    "amount": str(item["price_amount"]),
                    "currency": item["price_currency"]
                }
            }
            for item in sorted_itineraries
        ]
    }

    return response


async def sort_fastest(request: SortRequest):
    itineraries = request.itineraries
    sorting_type = request.sorting_type

    data = [
        {
            "id": itinerary.id,
            "duration_minutes": itinerary.duration_minutes,
            "price_amount": float(itinerary.price.amount),
            "price_currency": itinerary.price.currency
        }
        for itinerary in itineraries
    ]
    itineraries_df = pd.DataFrame(data)

    sorted_indices = np.argsort(itineraries_df["duration_minutes"].values)
    sorted_df = itineraries_df.iloc[sorted_indices].reset_index(drop=True)
    sorted_itineraries = sorted_df.to_dict(orient="records")

    response = {
        "sorting_type": sorting_type,
        "sorted_itineraries": [
            {
                "id": item["id"],
                "duration_minutes": item["duration_minutes"],
                "price": {
                    "amount": str(item["price_amount"]),
                    "currency": item["price_currency"]
                }
            }
            for item in sorted_itineraries
        ]
    }

    return response


async def sort_best(request: SortRequest):
    itineraries = request.itineraries
    sorting_type = request.sorting_type
    price_weight = request.price_weight
    duration_weight = request.duration_weight

    data = [
        {
            "id": itinerary.id,
            "duration_minutes": itinerary.duration_minutes,
            "price_amount": float(itinerary.price.amount),
            "price_currency": itinerary.price.currency
        }
        for itinerary in itineraries
    ]
    itineraries_df = pd.DataFrame(data)

    await add_score_to_itineraries(itineraries_df, price_weight, duration_weight)

    sorted_indices = np.argsort(itineraries_df["score"].values)
    sorted_df = itineraries_df.iloc[sorted_indices].reset_index(drop=True)
    sorted_itineraries = sorted_df.drop(
        columns=["price_eur", "normalized_price_eur", "normalized_duration_minutes", "score"]
    ).to_dict(orient="records")

    response = {
        "sorting_type": sorting_type,
        "sorted_itineraries": [
            {
                "id": item["id"],
                "duration_minutes": item["duration_minutes"],
                "price": {
                    "amount": str(item["price_amount"]),
                    "currency": item["price_currency"]
                }
            }
            for item in sorted_itineraries
        ]
    }

    return response
