import os
import re
from pathlib import Path

import orjson
import pandas as pd
from src.currency import CurrencyRate
from deep_translator import GoogleTranslator
from src.ingame_price import GameInfo
from src.utils.clean_name import clean_game_name


def prepare_currency():
    os.makedirs("./data", exist_ok=True)
    output_path = "./data/currency_rates.csv"
    country_currency = CurrencyRate(path="./configs/countries_currency.csv").get_country_currency()
    country_currency.to_csv(output_path, index=False)
    return country_currency


def prepare_game_info(target_game: str, target_game_id: str):
    cleaned_name = clean_game_name(target_game)
    output_folder = "./data/game_info"
    os.makedirs(output_folder, exist_ok=True)
    if os.path.exists(f"{output_folder}/{cleaned_name}.csv"):
        game_info_data = pd.read_csv(f"{output_folder}/{cleaned_name}.csv")
        return game_info_data
    game_info_data = GameInfo(target_game=target_game).fetch_data()
    game_info_data.to_csv(f"{output_folder}/{target_game_id}.csv", index=False)
    return game_info_data


def update_all_data():
    game_data = pd.read_csv("./configs/game_data.csv")

    search_dict = {}
    for _, game in game_data.iterrows():
        target_game = game["name"]
        target_game_id = game["packageId"]
        cleaned_name = clean_game_name(target_game, target_game_id)
        prepare_game_info(target_game=target_game)

        search_dict[target_game] = cleaned_name
    search_dict = orjson.dumps(search_dict)
    with open("./data/search_dict.json", "wb") as f:
        f.write(search_dict)


if __name__ == "__main__":
    country_currency = prepare_currency()
    update_all_data()
