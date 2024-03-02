import os

import pandas as pd
from src.datamodule import DataBaseManager


def update_all_data():
    game_data = pd.read_csv("./configs/game_data.csv")

    # search_dict = {}
    for _, game in game_data.iterrows():
        target_game = game["name"]
        target_game_id = game["packageId"]
        dataloader = DataBaseManager(database_name="./data/ingame_price.db")
        dataloader.update_ingame_price(table_name=target_game)
        # cleaned_name = clean_game_name(target_game, target_game_id)
        # prepare_game_info(target_game=target_game)

    #     search_dict[target_game] = cleaned_name
    # search_dict = orjson.dumps(search_dict)
    # with open("./data/search_dict.json", "wb") as f:
    #     f.write(search_dict)


if __name__ == "__main__":
    update_all_data()
