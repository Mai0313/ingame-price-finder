import pandas as pd
from src.datamodule import DataBaseManager


def update_all_data() -> None:
    game_data = pd.read_csv("./configs/game_data.csv")

    for _, game in game_data.iterrows():
        target_game = game["name"]
        # target_game_id = game["packageId"]
        dataloader = DataBaseManager(database_name="./data/ingame_price.db")
        dataloader.update_ingame_price(table_name=target_game)


if __name__ == "__main__":
    update_all_data()
