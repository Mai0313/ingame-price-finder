import re
from typing import Union, Optional
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm  # Ensure you have tqdm installed
import orjson
import pandas as pd
from pydantic import Field, BaseModel, computed_field, model_validator
from price_parser import Price
from google_play_scraper import app


class GameInfo(BaseModel):
    game_list_path: str = Field(...)
    custom_games: Optional[list[str]] = Field(default=None)
    limit: Optional[int] = Field(default=None)

    @model_validator(mode="after")
    def check_rule(self):
        if self.custom_games and self.limit:
            if len(self.custom_games) != self.limit:
                raise ValueError(
                    f"Custom games and limit should be same \n The current limit is {self.limit} and the custom games are {len(self.custom_games)}"
                )

    @computed_field
    @property
    def game_lists(self) -> list[dict[str, Union[str, int]]]:
        with open(self.game_list_path, encoding="utf-8") as f:
            return orjson.loads(f.read())

    def fetch_single_game_info(self, game_data: dict, country: str) -> Optional[dict]:
        game_id = game_data["packageId"]
        game_name = game_data["name"]
        if self.custom_games and game_name not in self.custom_games:
            return None
        try:
            price = app(game_id, lang="en", country=country)["inAppProductPrice"]
            price = price.replace(" per item", "")
            lowest, highest = price.split(" - ")
            lowest = Price.fromstring(lowest).amount_float
            highest = Price.fromstring(highest).amount_float
            return {"Name": game_name, "country": country, "lowest": lowest, "highest": highest}
        except Exception:
            return None

    def fetch_game_info_parallel(self, country: str) -> pd.DataFrame:
        game_lists = self.game_lists[: self.limit] if self.limit else self.game_lists
        with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
            futures = {
                executor.submit(self.fetch_single_game_info, game_data=game, country=country): game
                for game in game_lists
            }
            game_info = []
            for future in tqdm(
                as_completed(futures), total=len(futures), desc=f"Fetching Game Info for {country}"
            ):
                result = future.result()
                if result:
                    game_info.append(result)
        return pd.DataFrame(game_info)


if __name__ == "__main__":
    country = "US"
    game_info_instance = GameInfo(
        game_list_path="./configs/gameList.json", custom_games=None, limit=None
    )
    game_info_df = game_info_instance.fetch_game_info_parallel(country=country)
    game_info_df.to_csv("./data/game_info.csv", index=False)
