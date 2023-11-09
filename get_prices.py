from concurrent.futures import ProcessPoolExecutor, as_completed

import orjson
import pandas as pd
from google_play_scraper import app
from omegaconf import OmegaConf
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
        pass
        return name, country, None


def get_game_info_to_df(country):
    games = get_game_list()
    with ProcessPoolExecutor() as executor:
        tasks = [executor.submit(get_game_info, (game, country)) for game in games]
        results = [
            r.result()
            for r in tqdm(as_completed(tasks), total=len(tasks), desc=f"Processing {country}")
        ]
    price_df = pd.DataFrame(results, columns=["遊戲名稱", "國家", "價格"])
    price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
    return price_df


def process_country(country):
    currency_name = country["currencyName"]
    country_name = country["countryName"]
    result = get_game_info_to_df(currency_name)
    result.to_csv(f"./data/{country_name}_info.csv", encoding="utf-8", index=None)


def get_game_info_to_csv(countries, parallel_countries=False):
    if parallel_countries:
        with ProcessPoolExecutor() as executor:
            tasks = [executor.submit(process_country, country) for country in countries]
            for _ in tqdm(as_completed(tasks), total=len(tasks), desc="Processing countries"):
                pass
    else:
        for country in countries:
            process_country(country)


if __name__ == "__main__":
    config = OmegaConf.load("./configs/setting.yaml")
    parallel_option = config.engine_setting.parallel

    countries = get_country()
    get_game_info_to_csv(countries, parallel_option)
