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
    output_path = "./data/currency_rates.csv"
    if os.path.exists(output_path):
        return output_path
    root_path = os.path.dirname(output_path)
    os.makedirs(root_path, exist_ok=True)
    country_currency = CurrencyRate(path="./configs/countries_currency.csv")
    country_currency = country_currency.get_country_currency()
    country_currency.to_csv(output_path, index=False)
    return country_currency


def prepare_game_info(target_game: str):
    cleaned_name = clean_game_name(target_game)
    output_folder = "./data/game_info"
    os.makedirs(output_folder, exist_ok=True)
    if os.path.exists(f"{output_folder}/{cleaned_name}.csv"):
        game_info_df = pd.read_csv(f"{output_folder}/{cleaned_name}.csv")
        return game_info_df
    game_info_instance = GameInfo(target_game=target_game)
    game_info_df = game_info_instance.fetch_game_info_parallel()
    country_currency = pd.read_csv("./data/currency_rates.csv")
    game_info_df = game_info_instance.postprocess_game_info(
        game_info_result=game_info_df, country_currency=country_currency
    )
    game_info_df.to_csv(f"{output_folder}/{cleaned_name}.csv", index=False)
    return game_info_df


def update_all_data():
    game_data = pd.read_csv("./configs/game_data.csv")
    for index, game in game_data.iterrows():
        target_game = game["name"]
        cleaned_name = clean_game_name(target_game)
        game_info_df = prepare_game_info(target_game=target_game)

        search_dict = {target_game: cleaned_name}
        search_dict = orjson.dumps(search_dict)
        with open("./data/search_dict.json", "wb") as f:
            f.write(search_dict)


if __name__ == "__main__":
    country_currency = prepare_currency()
    update_all_data()
