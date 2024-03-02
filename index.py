import gradio as gr
import pandas as pd
from src.ingame_price import GameInfo
from google_play_scraper import search


def search_and_process(app_id: str):
    game_info = search(app_id, lang="zh-TW", country="us", n_hits=10)
    game_data = pd.DataFrame(game_info)
    game_data = game_data.drop(
        [
            # "screenshots",
            "genre",
            "price",
            "free",
            "currency",
            "video",
            "videoImage",
            "descriptionHTML",
            "installs",
            "developer",
        ],
        axis=1,
    )
    game_data = game_data.rename(columns={"appId": "packageId", "title": "name"})
    game_data = game_data[["name", "packageId", "score", "description", "icon", "screenshots"]]
    return game_data


def update_output(app_id: str) -> pd.DataFrame:
    game_data = search_and_process(app_id)
    output_dataframe.value = game_data
    output_dataframe.visible = True
    return game_data


def get_user_selected_row(output_dataframe: pd.DataFrame, evt: gr.SelectData):
    user_selected_block = evt.value
    output_dataframe = output_dataframe.query(
        "name == @user_selected_block or packageId == @user_selected_block or icon == @user_selected_block"
    )
    selected_game = output_dataframe["name"].values[0]
    icon_url = output_dataframe["icon"].values[0]
    selected_game_screenshots = output_dataframe["screenshots"].values[0]
    return user_selected_block, icon_url, selected_game_screenshots


def save_data(app_id: str, selected_row: str):
    try:
        game_data = update_output(selected_row)
        selected_game_data = game_data.query("packageId == @selected_row or name == @selected_row")
        selected_game_data = selected_game_data.drop(["icon", "score", "description"], axis=1)

        target_game = selected_game_data["name"].values[0]
        game_info_instance = GameInfo(target_game=target_game)
        game_info_data = game_info_instance.fetch_game_info_parallel()
        country_currency = pd.read_csv("./data/currency_rates.csv")
        game_info_data = game_info_instance.postprocess_game_info(
            game_info_result=game_info_data, country_currency=country_currency
        )

        original_game_data = pd.read_csv("./configs/game_data.csv")
        merged_data = pd.concat([original_game_data, selected_game_data], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=["packageId"], keep="last")
        merged_data.to_csv("./configs/game_data_test.csv", index=False)
        app_id = selected_game_data["name"].values[0]
        result_markdown = f"""
        # 🎉 {app_id} 已成功加入遊戲列表
        """
        return result_markdown, game_info_data
    except Exception as e:
        result_markdown = f"""
        # ⚠️ 加入列表時發生錯誤: {e!s}
        """
        return result_markdown, None


def load_price_data():
    root_path = "./data/game_info"


with gr.Blocks() as demo:
    with gr.Row():
        app_id_input = gr.Textbox(
            label="APP 名稱", placeholder="請輸入遊戲名稱或遊戲ID...", value="原神"
        )
        search_button = gr.Button("搜尋")
    output_dataframe = gr.DataFrame(interactive=False)

    selected_row_input = gr.Textbox(
        label="你選擇的是: ", placeholder="請點選上方任意行選擇要儲存的遊戲..."
    )
    with gr.Tab("遊戲圖標"):
        icon_url = gr.Image(height=256, width=256)
    with gr.Tab("遊戲截圖"):
        selected_game_screenshots = gr.Gallery(columns=[6], rows=[6], height="auto")
    with gr.Tab("價目表"):
        game_info_data = gr.DataFrame(interactive=False)

    save_result = gr.Markdown()
    save_button = gr.Button("新增遊戲資訊")

    search_button.click(fn=update_output, inputs=app_id_input, outputs=output_dataframe)
    output_dataframe.select(
        get_user_selected_row,
        inputs=[output_dataframe],
        outputs=[selected_row_input, icon_url, selected_game_screenshots],
    )
    save_button.click(
        fn=save_data,
        inputs=[app_id_input, selected_row_input],
        outputs=[save_result, game_info_data],
    )

demo.launch(share=True, server_name="0.0.0.0")
