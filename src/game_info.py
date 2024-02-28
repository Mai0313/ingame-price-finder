import re
from typing import Union, Optional

import orjson
import pandas as pd
from pydantic import Field, BaseModel, computed_field
from google_play_scraper import app


class GameInfo(BaseModel):
    game_list_path: str = Field(...)

    @computed_field
    @property
    def game_lists(self) -> list[dict[str, Union[str, int]]]:
        with open(self.game_list_path, encoding="utf-8") as f:
            return orjson.loads(f.read())

    def fetch_game_info(
        self, country: str, selected_games: Optional[Union[str, int]] = None
    ) -> pd.DataFrame:
        game_info = []
        for idx, game_list in enumerate(self.game_lists):
            game_id = game_list["packageId"]
            game_name = game_list["name"]
            if selected_games:
                if isinstance(selected_games, str):
                    if game_name != selected_games:
                        pass
                if isinstance(selected_games, int):
                    if idx == selected_games:
                        break
            try:
                price = app(game_id, lang="en", country=country)["inAppProductPrice"]  # type: str
                price = price.replace(" per item", "")
                lowest, highest = price.split(" - ")
                lowest = re.findall(r"\d+\.?\d*", lowest)[0]
                highest = re.findall(r"\d+\.?\d*", highest)[0]
                info = {
                    "Name": game_name,
                    "country": country,
                    "lowest": lowest,
                    "highest": highest,
                }
                game_info.append(info)
            except Exception:
                continue
        game_info = pd.DataFrame(game_info)
        return game_info


if __name__ == "__main__":
    country = "US"

    game_info = GameInfo(game_list_path="./configs/gameList.json")
    game_info = game_info.fetch_game_info(country=country, selected_games=None)
    game_info.to_csv("./data/game_info.csv", index=False)
