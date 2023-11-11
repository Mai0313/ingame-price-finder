import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import orjson
import pandas as pd
from google_play_scraper import app
from omegaconf import OmegaConf
from pydantic import BaseModel
from rich.progress import Progress


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
    country_name: str

    def get_game_price_v1(self):
        games = get_game_list()
        results = []
        with Progress() as progress:
            task = progress.add_task(f"Processing {self.country}...", total=len(games))
            for game in games:
                input_args = (game, self.country)
                name, country, price = get_game_info(input_args)
                data = {"遊戲名稱": name, "國家": country, "價格": price}
                results.append(data)
                progress.update(task, advance=1)
        price_df = pd.DataFrame(results)
        price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
        return price_df

    def get_game_price_v2(self):
        games = get_game_list()
        with ProcessPoolExecutor() as executor, Progress() as progress:
            tasks = [executor.submit(get_game_info, (game, self.country)) for game in games]
            task = progress.add_task(f"Processing {self.country_name}...", total=len(tasks))
            results = []
            for future in as_completed(tasks):
                result = future.result()
                results.append(result)
                progress.update(task, advance=1)
        price_df = pd.DataFrame(results, columns=["遊戲名稱", "國家", "價格"])
        price_df["價格"] = price_df["價格"].str.split("-").str[-1].str.split(" ").str[1]
        return price_df


class GamePriceGrabber(BaseModel):
    countries: list[dict]
    parallel_countries: bool
    parallel_games: bool
    output_path: str

    def _get_game_info(self, country):
        currency_name = country["currencyName"]
        country_name = country["countryName"]
        processor = GamePriceProcessor(country=currency_name, country_name=country_name)
        if self.parallel_games:
            result = processor.get_game_price_v2()
        else:
            result = processor.get_game_price_v1()
        result.to_csv(
            f"{self.output_path!s}/{country_name}_info.csv", encoding="utf-8", index=None
        )

    def get_game_info_to_csv(self):
        os.makedirs(f"{self.output_path!s}", exist_ok=True)
        if self.parallel_countries:
            with ProcessPoolExecutor() as executor, Progress() as progress:
                tasks = [
                    executor.submit(self._get_game_info, country) for country in self.countries
                ]
                task = progress.add_task("Processing countries...", total=len(tasks))
                for _ in as_completed(tasks):
                    progress.update(task, advance=1)
        else:
            for country in self.countries:
                self._get_game_info(country)


if __name__ == "__main__":
    config = OmegaConf.load("./configs/setting.yaml")
    parallel_countries = config.engine_setting.parallel_countries
    parallel_games = config.engine_setting.parallel_games
    output_path = config.config_path.games_price_output_path
    countries = get_country()
    GamePriceGrabber(
        countries=countries,
        parallel_countries=parallel_countries,
        parallel_games=parallel_games,
        output_path=output_path,
    ).get_game_info_to_csv()
