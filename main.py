from src.ingame_price import GameInfoUpdater
from src.currency_core import CurrencyCore

if __name__ == "__main__":
    currency_rate = CurrencyCore(country_name="usd")
    currency_rate.fetch_currency_rates()
    currency_rate.get_avali_currency()
    game_info_fetcher = GameInfoUpdater(game_name="天堂W", country="us")
    game_info_fetcher.fetch_game_info()
