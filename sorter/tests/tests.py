import pytest
import pandas as pd
from unittest.mock import patch
from sorter.api.utils import (
    convert_currency,
    convert_prices_async,
)
from sorter.api.v1.endpoints.sort_itineriraries import sort_cheapest, sort_fastest, sort_best
from sorter.schemas.itinerirary_schemas import SortRequest, Itinerary, Price


class TestUtils:
    @pytest.mark.asyncio
    async def test_convert_currency_async_usd_to_eur(self):
        with patch("sorter.api.utils.CurrencyConverter") as MockCurrencyConverter:
            mock_instance = MockCurrencyConverter.return_value
            mock_instance.convert.return_value = 85.0

            result = await convert_currency("USD", 100, "EUR")
            assert result == 85.0

    @pytest.mark.asyncio
    async def test_convert_currency_async_invalid_currency(self):
        with patch("sorter.api.utils.CurrencyConverter") as MockCurrencyConverter:
            mock_instance = MockCurrencyConverter.return_value
            mock_instance.convert.side_effect = ValueError("Invalid currency")
            with pytest.raises(ValueError):
                await convert_currency("INVALID", 100, "EUR")

    @pytest.mark.asyncio
    async def test_convert_prices_async_valid(self):
        with patch("sorter.api.utils.convert_currency") as mock_convert_currency:
            mock_convert_currency.return_value = 85.0
            itineraries_df = pd.DataFrame({
                "price_currency": ["USD", "USD"],
                "price_amount": [100, 200]
            })
            await convert_prices_async(itineraries_df)
            assert itineraries_df["price_eur"].tolist() == [85.0, 85.0]

    @pytest.mark.asyncio
    async def test_convert_prices_async_invalid_currency(self):
        with patch("sorter.api.utils.convert_currency") as mock_convert_currency:
            mock_convert_currency.side_effect = ValueError("Invalid currency")
            itineraries_df = pd.DataFrame({
                "price_currency": ["INVALID", "USD"],
                "price_amount": [100, 200]
            })
            with pytest.raises(ValueError):
                await convert_prices_async(itineraries_df)


class TestEndpoints:
    @pytest.mark.asyncio
    async def test_sort_cheapest_itineraries(self):
        with patch("sorter.api.utils.convert_prices_async") as mock_convert_prices_async:
            mock_convert_prices_async.return_value = None
            request = SortRequest(
                itineraries=[
                    Itinerary(id="1", duration_minutes=120, price=Price(amount=100, currency="CZK")),
                    Itinerary(id="2", duration_minutes=90, price=Price(amount=80, currency="CZK"))
                ],
                sorting_type="cheapest"
            )
            result = await sort_cheapest(request)
            assert result["sorted_itineraries"][0]["id"] == "2"

    @pytest.mark.asyncio
    async def test_sort_fastest_itineraries(self):
        request = SortRequest(
            itineraries=[
                Itinerary(id="1", duration_minutes=120, price=Price(amount=100, currency="CZK")),
                Itinerary(id="2", duration_minutes=90, price=Price(amount=80, currency="CZK"))
            ],
            sorting_type="fastest"
        )
        result = await sort_fastest(request)
        assert result["sorted_itineraries"][0]["id"] == "2"

    @pytest.mark.asyncio
    async def test_sort_best_itineraries(self):
        with patch("sorter.api.utils.add_score_to_itineraries") as mock_add_score_to_itineraries:
            mock_add_score_to_itineraries.return_value = None
            request = SortRequest(
                itineraries=[
                    Itinerary(id="1", duration_minutes=120, price=Price(amount=100, currency="CZK")),
                    Itinerary(id="2", duration_minutes=90, price=Price(amount=80, currency="CZK"))
                ],
                sorting_type="best",
                price_weight=0.5,
                duration_weight=0.5
            )
            result = await sort_best(request)
            assert result["sorted_itineraries"][0]["id"] == "2"
