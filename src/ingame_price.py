import os
from typing import Union, Optional
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
from pydantic import Field, BaseModel, computed_field, model_validator
from price_parser import Price
from rich.progress import Progress
from google_play_scraper import app


class GameInfo(BaseModel):
    target_game: str = Field(
        ...,
        title="Target Game",
        description="The name of the game you want to fetch the information for",
    )
    target_game_id: Optional[str] = Field(default=None)

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
        game_data = game_data.query("@self.target_game in name or @self.target_game in packageId")
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
            price = app(game_id, lang="zh-TW", country=country)["inAppProductPrice"]  # type: str
            price = price.replace("每個項目 ", "")
            lowest, highest = price.split(" - ")
            lowest = Price.fromstring(lowest).amount_float
            highest = Price.fromstring(highest).amount_float
            return {"Name": game_name, "country": country, "lowest": lowest, "highest": highest}
        except Exception:
            return {"Name": game_name, "country": country, "lowest": None, "highest": None}

    @classmethod
    def get_price_details(
        cls, country_currency: pd.DataFrame, game_info: pd.DataFrame
    ) -> pd.DataFrame:
        price_details = pd.merge(
            country_currency, game_info, left_on="CountryCode", right_on="country", how="left"
        )
        price_details = price_details[
            [
                "Name",
                "country",
                "CountryCode",
                "Currency",
                "Currency_CN",
                "Updated_date",
                "lowest",
                "highest",
                "JCB",
                "萬事達",
                "VISA",
            ]
        ]
        price_details["JCB"] = price_details["JCB"].astype(float)
        price_details["萬事達"] = price_details["萬事達"].astype(float)
        price_details["VISA"] = price_details["VISA"].astype(float)

        price_details["JCB 最高價"] = price_details["JCB"] * price_details["highest"]
        price_details["萬事達 最高價"] = price_details["萬事達"] * price_details["highest"]
        price_details["VISA 最高價"] = price_details["VISA"] * price_details["highest"]

        price_details["JCB 最低價"] = price_details["JCB"] * price_details["lowest"]
        price_details["萬事達 最低價"] = price_details["萬事達"] * price_details["lowest"]
        price_details["VISA 最低價"] = price_details["VISA"] * price_details["lowest"]

        price_details = price_details.drop(["JCB", "萬事達", "VISA", "country"], axis=1)
        price_details = price_details.drop_duplicates()
        price_details = price_details.dropna(
            subset=[
                "Name",
                "JCB 最高價",
                "萬事達 最高價",
                "VISA 最高價",
                "JCB 最低價",
                "萬事達 最低價",
                "VISA 最低價",
            ],
            how="any",
        )
        return price_details

    def fetch_data(self, country_currency: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if self.target_game_id is None:
            self.target_game, self.target_game_id = self.game_details
        game_information = []
        with Progress() as progress:
            task = progress.add_task(
                f"Fetching {self.target_game} information", total=len(self.country_codes)
            )
            with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
                futures = [
                    executor.submit(
                        self.fetch_single_game_info,
                        game_id=self.target_game_id,
                        game_name=self.target_game,
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

        if country_currency is not None:
            game_information = self.get_price_details(
                country_currency=country_currency, game_info=game_information
            )
        return game_information


if __name__ == "__main__":
    target_game = "原神"
    country_currency = pd.read_csv("./data/currency_rates.csv")
    game_info_instance = GameInfo(target_game=target_game)
    game_info_df = game_info_instance.fetch_data(country_currency=country_currency)
