import os

import pandas as pd
from rich.console import Console
from src.currency import CurrencyRate
from src.game_info import GameInfo
from src.price_details import PriceDetails

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
    game_info = GameInfo(game_list_path="./configs/gameList.json")
    country_details = pd.read_csv("./configs/countries_currency.csv")["CountryCode"].values

    for country_code in country_details:
        console.log(f"Fetching game info for {country_code}")
        game_info = game_info.fetch_game_info(country=country_code, selected_games=None)
        os.makedirs("./data/game_info", exist_ok=True)
        game_info.to_csv(f"./data/game_info/{country_code}.csv", index=False)
        price_details = PriceDetails(
            country_currency=country_currency, game_info=f"./data/game_info/{country_code}.csv"
        )
        price_details = price_details.get_price_details()
        os.makedirs("./data/price_details", exist_ok=True)
        price_details.to_csv(f"./data/price_details/{country_code}.csv", index=False)


if __name__ == "__main__":
    country_currency = prepare_currency()
    main(country_currency=country_currency)
