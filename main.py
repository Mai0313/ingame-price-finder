import os

import pandas as pd
from rich.console import Console
from src.currency import CurrencyRate
from src.game_info import GameInfo

from datamodule import PriceDetails

console = Console()


def prepare_currency():
    output_path = "./data/currency_rates.csv"
    if os.path.exists(output_path):
        return output_path
    root_path = os.path.dirname(output_path)
    os.makedirs(root_path, exist_ok=True)
    country_currency = CurrencyRate(path="./configs/countries_currency.csv")
    country_currency = country_currency.get_country_currency()
    country_currency.to_csv(output_path, index=False)
    return output_path


def main(country_currency: str):
    game_info_grabber = GameInfo(
        game_list_path="./configs/gameList.json", custom_games=None, limit=None
    )
    country_details = pd.read_csv("./configs/countries_currency.csv")
    country_details = country_details.dropna(subset=["CountryCode"])
    os.makedirs("./data/game_info", exist_ok=True)
    os.makedirs("./data/price_details", exist_ok=True)

    for index, row in country_details.iterrows():
        country_code = row["CountryCode"]
        game_info_path = f"./data/game_info/{country_code}.csv"
        price_details_path = f"./data/price_details/{country_code}.csv"
        if not os.path.exists(game_info_path):
            console.log(f"Fetching game info for {country_code}")
            game_info = game_info_grabber.fetch_game_info_parallel(country=country_code)
            game_info.to_csv(game_info_path, index=False)
        if not os.path.exists(price_details_path):
            price_details = PriceDetails(
                country_currency=country_currency, game_info=game_info_path
            )
            price_details = price_details.get_price_details()
            price_details.to_csv(price_details_path, index=False)


if __name__ == "__main__":
    country_currency = prepare_currency()
    main(country_currency=country_currency)
