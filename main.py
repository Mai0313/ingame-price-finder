from src.currency_core import CurrencyCore

if __name__ == "__main__":
    currency_rate = CurrencyCore()
    currency_rate_list = currency_rate.fetch_currency_rates(currency_name_en="all")
    # currency_rate_list = [f.model_dump() for f in currency_rate_list]
    # game_info_fetcher = GameInfoUpdater(game_name="天堂W", country="us")
    # game_info_result = game_info_fetcher.fetch_game_info()
    # game_info_result = [f.model_dump() for f in game_info_result]
