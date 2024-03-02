import gradio as gr
import orjson
import pandas as pd


# 讀取遊戲列表
def game_list_keys() -> list[str]:
    with open("./data/search_dict.json", "rb") as f:
        search_dict = orjson.loads(f.read())  # type: dict[str, str]
    return list(search_dict.keys())


def filter_games(selected_game):
    with open("./data/search_dict.json", "rb") as f:
        search_dict = orjson.loads(f.read())  # type: dict[str, str]
    game_info_path = f"./data/game_info/{search_dict[selected_game]}.csv"
    game_info_data = pd.read_csv(game_info_path)
    return game_info_data


search_list = game_list_keys()

with gr.Blocks() as demo:
    selected_game = gr.Dropdown(choices=search_list, label="選擇遊戲")
    game_info = gr.DataFrame(label="價格訊息")

    def update_game_info(selected_game):
        return filter_games(selected_game)

    selected_game.select(update_game_info, inputs=[selected_game], outputs=[game_info])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8081, debug=True)
