import logging
import asyncio
from currency_converter import CurrencyConverter

logger = logging.getLogger(__name__)


async def convert_currency(from_currency:str, amount_to_convert:float | int, to_currency:str | None = "EUR") -> float:
    # TODO: Use better solution for exchange rates like forex-python?
    # Using currency_converter for now because of the simplicity of task and having offline currency rates
    """
    Convert an amount from one currency to another.
    """
    try:
        result = CurrencyConverter().convert(amount_to_convert, from_currency, to_currency)
    except Exception as e:
        logger.error(f"Error while converting {amount_to_convert=} {from_currency=} {to_currency=}: {e}")
        raise e

    return result


async def convert_prices_async(itineraries_df):
    """
    Convert all prices in a DataFrame to a common currency (EUR) asynchronously.
    """
    tasks = [
        convert_currency(row["price_currency"], row["price_amount"])
        for _, row in itineraries_df.iterrows()
    ]
    itineraries_df["price_eur"] = await asyncio.gather(*tasks)


def normalize_column(dataframe, column_name):
    """
    Normalize a column in a DataFrame to a range between 0 and 1 for faster sorting.
    """
    min_value = dataframe[column_name].min()
    max_value = dataframe[column_name].max()
    dataframe[f"normalized_{column_name}"] = (dataframe[column_name] - min_value) / (max_value - min_value)
    return dataframe


async def add_score_to_itineraries(itineraries_df, price_weight=0.5, duration_weight=0.5):
    """
    Add a score to each itinerary based on the price and duration weights.
    """
    await convert_prices_async(itineraries_df)
    itineraries_df = normalize_column(itineraries_df, "price_eur")
    itineraries_df = normalize_column(itineraries_df, "duration_minutes")
    itineraries_df["score"] = (price_weight * itineraries_df["normalized_price_eur"]) + (
            duration_weight * itineraries_df["normalized_duration_minutes"]
    )
    return itineraries_df
