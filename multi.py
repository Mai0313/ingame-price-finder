import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
from google_play_scraper import app
from tqdm import tqdm


def get_game_list():
    with open("data/gameList.json", encoding="utf-8") as f:
        return json.load(f)


def get_country():
    with open("data/currencyRate.json", encoding="utf-8") as f:
        return json.load(f)


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
    CurrencyName = country["currencyName"]
    Country = country["countryName"]
    result = get_game_info_to_df(CurrencyName)
    result.to_csv(f"output/{Country}_info.csv", encoding="utf-8", index=None)


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
    parser = argparse.ArgumentParser(description="Choose parallel processing mode.")
    parser.add_argument(
        "--parallel-countries",
        action="store_true",
        help="Enable parallel processing of multiple countries.",
    )
    args = parser.parse_args()
    import time

    start = time.time()

    countries = get_country()
    get_game_info_to_csv(countries, args.parallel_countries)

    end = time.time() - start
    print(end)
