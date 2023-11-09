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


def get_game_info(args):
    game, country = args
    name, gameid, _ = game["name"], game["packageId"], game["id"]
    try:
        price = app(gameid, lang="en", country=country)["inAppProductPrice"]
        return name, country, price
    except Exception as e:
        return name, country, None


def get_game_price(country):
    games = get_game_list()
    results = []
    for game in tqdm(games, desc=f"Processing {country}"):
        input_args = (game, country)
        name, country, price = get_game_info(input_args)
        data = {"遊戲名稱": name, "國家": country, "價格": price}
        results.append(data)
    price_df = pd.DataFrame(results)
    price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
    return price_df


def get_game_info_to_csv(countries):
    os.makedirs("./data", exist_ok=True)
    for country in countries:
        CurrencyName = country["currencyName"]
        Country = country["countryName"]
        result = get_game_price(CurrencyName)
        result.to_csv(f"./data/{Country}_info.csv", encoding="utf-8", index=None)


if __name__ == "__main__":
    countries = get_country()
    get_game_info_to_csv(countries)
