from src.ingame_price import GameInfoUpdater


def test_fetch_game_info():
    game_info_fetcher = GameInfoUpdater(game_name="天堂W", country="us")
    game_info_fetcher.fetch_game_info()
