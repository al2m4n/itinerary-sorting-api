import json
import random

num_itineraries = 100
currencies = ["EUR", "USD", "CZK", "GBP", "JPY", "AUD", "CAD"]

itineraries = [
    {
        "id": f"itinerary_{i+1}",
        "duration_minutes": random.randint(60, 480),  # Random duration between 1 and 8 hours
        "price": {
            "amount": str(random.randint(100, 10000)),  # Random amount between 100 and 10000
            "currency": random.choice(currencies)
        }
    }
    for i in range(num_itineraries)
]

payload = {
    "sorting_type": "best",
    "price_weight": 0.5,
    "duration_weight": 0.5,
    "itineraries": itineraries
}

with open(f"{num_itineraries}_itineraries_payload.json", "w") as f:
    json.dump(payload, f, indent=2)

print(f"Payload with 1000 itineraries saved to {num_itineraries}_itineraries_payload.json")
