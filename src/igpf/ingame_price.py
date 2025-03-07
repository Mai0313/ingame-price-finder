import yaml
import logfire
from pydantic import Field, BaseModel, computed_field
from price_parser import Price
import google_play_scraper as gps

from .typings.game import GameInfo, GamePriceInfo

logfire.configure()


class GameInfoUpdater(BaseModel):
    game_id: str | None = Field(
        default=None,
        title="Package ID",
        description="Package ID from play store",
        examples=["com.ncsoft.lineagew"],
        deprecated=False,
    )
    game_name: str | None = Field(
        default=None,
        title="Game Name",
        description="Game Name from play store",
        examples=["天堂W"],
        deprecated=False,
    )
    country: str = Field(..., title="Country")

    @computed_field
    @property
    def game_info_list(self) -> list[GameInfo]:
        game_info_list: list[GameInfo] = []
        with open("./configs/gameList.json", encoding="utf-8") as f:
            game_list = yaml.safe_load(f)
            for game in game_list:
                game_info = GameInfo(**game)
                game_info_list.append(game_info)
        if self.game_name:
            return [info for info in game_info_list if self.game_name in game_info.game_name]
        if self.game_id:
            return [info for info in game_info_list if self.game_id in game_info.game_id]
        return game_info_list

    def __fetch(self) -> GamePriceInfo:
        try:
            if not self.game_id or not self.game_name:
                raise logfire.exception("game_id or game_name is missing")
            price = gps.app(self.game_id, lang="zh-TW", country=self.country)["inAppProductPrice"]  # type: str
            price = price.replace("每個項目 ", "")
            lowest_string, highest_string = price.split(" - ")
            lowest = Price.fromstring(lowest_string).amount_float
            highest = Price.fromstring(highest_string).amount_float
            return GamePriceInfo(
                name=self.game_name, country=self.country, lowest=lowest, highest=highest
            )
        except Exception:
            return GamePriceInfo(
                name=self.game_name, country=self.country, lowest=0.0, highest=0.0
            )

    def fetch_game_info(self) -> list[GamePriceInfo]:
        game_info_result = []
        if self.game_id and self.game_name:
            fetched_info = self.__fetch()
            return [fetched_info]
        for game_info in self.game_info_list:
            self.game_id = game_info.game_id
            self.game_name = game_info.game_name
            result = self.__fetch()
            game_info_result.append(result)
            logfire.info("Fetching Game Info", **result.model_dump())
        return game_info_result


if __name__ == "__main__":
    game_info_fetcher = GameInfoUpdater(country="us")
    game_info_fetcher.fetch_game_info()
