import os

import orjson
import pandas as pd
from google_play_scraper import app
from tqdm import tqdm


def get_game_list():
    with open("./configs/gameList.json", "rb") as file:
        json_data = file.read()
        data = orjson.loads(json_data)
    return data


def get_country():
    with open("./configs/currencyRate.json", "rb") as file:
        json_data = file.read()
        data = orjson.loads(json_data)
    return data


def get_game_info(name, country):
    return app(name, lang="en", country=country)


def get_game_info_to_df(country):
    games = get_game_list()
    result = pd.DataFrame()
    for game in tqdm(games, desc=f"Processing {country}"):
        name, gameid, _ = game["name"], game["packageId"], game["id"]
        country = country
        try:
            price = get_game_info(gameid, country)["inAppProductPrice"]
        except Exception as e:
            continue
        price_df = pd.DataFrame([[name, country, price]], columns=["遊戲名稱", "國家", "價格"])
        price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
        result = pd.concat([result, price_df])
    return result


def get_game_info_to_csv(countries):
    os.makedirs("./data", exist_ok=True)
    for country in countries:
        CurrencyName = country["currencyName"]
        Country = country["countryName"]
        result = get_game_info_to_df(CurrencyName)
        result.to_csv(f"./data/{Country}_info.csv", encoding="utf-8", index=None)


if __name__ == "__main__":
    countries = get_country()
    get_game_info_to_csv(countries)
