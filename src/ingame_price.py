import re
from typing import Union, Optional
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
from pydantic import Field, BaseModel, computed_field, model_validator
from price_parser import Price
from rich.progress import Progress
from google_play_scraper import app
from src.utils.datamodule import PriceDetails


class GameInfo(BaseModel):
    target_game: str = Field(
        ...,
        title="Target Game",
        description="The name of the game you want to fetch the information for",
    )

    @computed_field
    @property
    def country_codes(self) -> list[str]:
        country_codes = pd.read_csv("./configs/countries_currency.csv")
        country_codes = country_codes.dropna(subset=["CountryCode"])
        country_codes = country_codes["CountryCode"].values.tolist()
        return country_codes

    @computed_field
    @property
    def game_details(self) -> tuple[str, Union[str, None]]:
        game_data = pd.read_csv("./configs/game_data.csv")
        game_data = game_data.query("@self.target_game in name")
        if not game_data.empty:
            game_name = game_data["name"].values[0]
            game_id = game_data["packageId"].values[0]
            return game_name, game_id
        else:
            return self.target_game, None

    @classmethod
    def fetch_single_game_info(
        cls, game_id: str, game_name: str, country: str
    ) -> dict[str, Union[str, float, None]]:
        """This function will only get the price of a game.

        game_id (str): this is the packageId of the game
        game_name (str): this is the name of the game
        """
        try:
            price = app(game_id, lang="en", country=country)["inAppProductPrice"]  # type: str
            price = price.replace(" per item", "")
            lowest, highest = price.split(" - ")
            lowest = Price.fromstring(lowest).amount_float
            highest = Price.fromstring(highest).amount_float
            return {"Name": game_name, "country": country, "lowest": lowest, "highest": highest}
        except Exception:
            return {"Name": game_name, "country": country, "lowest": None, "highest": None}

    def fetch_game_info_parallel(self) -> pd.DataFrame:
        target_game_name, target_game_id = self.game_details
        game_information = []
        # change to rich progress bar
        with Progress() as progress:
            task = progress.add_task(
                f"Fetching {target_game_name} information", total=len(self.country_codes)
            )
            with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
                futures = [
                    executor.submit(
                        self.fetch_single_game_info,
                        game_id=target_game_id,
                        game_name=target_game_name,
                        country=country_code,
                    )
                    for country_code in self.country_codes
                ]
                for future in as_completed(futures):
                    game_info = future.result()
                    game_information.append(game_info)
                    progress.update(task, advance=1)
        game_information = pd.DataFrame(game_information)
        game_information = game_information.dropna(subset=["lowest", "highest"])
        return game_information

    def postprocess_game_info(
        self, game_info_result: pd.DataFrame, country_currency: pd.DataFrame
    ):
        ingame_price = PriceDetails(
            country_currency=country_currency, game_info=game_info_result
        ).get_price_details()
        return ingame_price


if __name__ == "__main__":
    target_game = "原神"
    game_info_instance = GameInfo(target_game=target_game)
    game_info_df = game_info_instance.fetch_game_info_parallel()
    country_currency = pd.read_csv("./data/currency_rates.csv")
    game_info_df = game_info_instance.postprocess_game_info(
        game_info_result=game_info_df, country_currency=country_currency
    )
    game_info_df.to_csv(f"./data/{target_game}.csv", index=False)
