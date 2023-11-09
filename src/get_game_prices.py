import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import orjson
import pandas as pd
from google_play_scraper import app
from omegaconf import OmegaConf
from pydantic import BaseModel
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


class GamePriceProcessor(BaseModel):
    country: str

    def get_game_price_v1(self):
        games = get_game_list()
        results = []
        for game in tqdm(games, desc=f"Processing {self.country}"):
            input_args = (game, self.country)
            name, country, price = get_game_info(input_args)
            data = {"遊戲名稱": name, "國家": country, "價格": price}
            results.append(data)
        price_df = pd.DataFrame(results)
        price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
        return price_df

    def get_game_price_v2(self):
        games = get_game_list()
        with ProcessPoolExecutor() as executor:
            tasks = [executor.submit(get_game_info, (game, self.country)) for game in games]
            results = [
                r.result()
                for r in tqdm(
                    as_completed(tasks), total=len(tasks), desc=f"Processing {self.country}"
                )
            ]
        price_df = pd.DataFrame(results, columns=["遊戲名稱", "國家", "價格"])
        price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
        return price_df


class GamePriceGrabber(BaseModel):
    countries: list[dict]
    parallel_option: bool

    def get_game_info_to_csv(self):
        os.makedirs("./data", exist_ok=True)
        for country in self.countries:
            currency_name = country["currencyName"]
            country_name = country["countryName"]
            processor = GamePriceProcessor(country=currency_name)
            if self.parallel_option:
                result = processor.get_game_price_v2()
            else:
                result = processor.get_game_price_v1()
            result.to_csv(f"./data/{country_name}_info.csv", encoding="utf-8", index=None)


if __name__ == "__main__":
    config = OmegaConf.load("./configs/setting.yaml")
    parallel_option = config.engine_setting.parallel
    countries = get_country()
    GamePriceGrabber(countries=countries, parallel_option=parallel_option).get_game_info_to_csv()
