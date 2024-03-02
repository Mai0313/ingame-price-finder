import gradio as gr
import pandas as pd
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
        original_game_data = pd.read_csv("./configs/game_data.csv")
        merged_data = pd.concat([original_game_data, selected_game_data], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=["packageId"], keep="last")
        merged_data.to_csv("./configs/game_data_test.csv", index=False)
        app_id = selected_game_data["name"].values[0]
        return f"{app_id} 已成功加入遊戲列表"
    except Exception as e:
        return f"加入列表時發生錯誤: {e!s}"


with gr.Blocks() as demo:
    with gr.Row():
        app_id_input = gr.Textbox(
            label="APP 名稱", placeholder="請輸入遊戲名稱或遊戲ID...", value="原神"
        )
        search_button = gr.Button("搜尋")
    output_dataframe = gr.DataFrame(interactive=False)

    search_button.click(fn=update_output, inputs=app_id_input, outputs=output_dataframe)
    selected_row_input = gr.Textbox(label="你選擇的是: ", placeholder="請點選上方任意行選擇要儲存的遊戲...")
    icon_url = gr.Image(height=256, width=256)
    selected_game_screenshots = gr.Gallery(columns=[6], rows=[6], height="auto")
    output_dataframe.select(
        get_user_selected_row,
        inputs=[output_dataframe],
        outputs=[selected_row_input, icon_url, selected_game_screenshots],
    )
    save_result = gr.Textbox()

    save_button = gr.Button("Save Selected Row")
    save_button.click(fn=save_data, inputs=[app_id_input, selected_row_input], outputs=save_result)

demo.launch(share=False, server_name="0.0.0.0")
