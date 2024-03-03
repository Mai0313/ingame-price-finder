import gradio as gr
import pandas as pd
from src.datamodule import DataBaseManager
from google_play_scraper import search

auth_message = "登入管理面板"
auth = [("admin", "admin"), ("user", "user")]


def search_and_process(app_id: str):
    game_info = search(app_id, lang="zh-TW", country="TW", n_hits=5)
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
    cols = ["name", "packageId", "icon", "screenshots", "description", "score"]
    condition = output_dataframe[cols].apply(lambda x: x == user_selected_block)
    user_selected_row = output_dataframe[condition.any(axis=1)]
    if user_selected_row.empty:
        gr.Error("請選擇 APP 名稱 或 APP ID")

    selected_game = user_selected_row["name"].values[0]
    icon_url = user_selected_row["icon"].values[0]
    selected_game_screenshots = user_selected_row["screenshots"].values[0]
    selected_game_screenshots = [icon_url, *selected_game_screenshots]
    return (
        user_selected_row,
        selected_game,
        user_selected_block,
        icon_url,
        selected_game_screenshots,
    )


def save_data(selected_game_data: pd.DataFrame):
    try:
        selected_game_data = selected_game_data.drop(
            ["icon", "score", "description", "screenshots"], axis=1
        )
        target_game = selected_game_data["name"].values[0]
        target_game_id = selected_game_data["packageId"].values[0]
        dataloader = DataBaseManager(database_name="./data/ingame_price.db")
        game_info_data = dataloader.update_ingame_price(
            table_name=target_game, target_game_id=target_game_id
        )
        if game_info_data is not None:
            game_info_data = game_info_data.drop(
                ["CountryCode", "Currency", "Updated_date"], axis=1
            )

        original_game_data = pd.read_csv("./configs/game_data.csv")
        merged_data = pd.concat([original_game_data, selected_game_data], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=["packageId"], keep="first")
        merged_data.to_csv("./configs/game_data.csv", index=False)
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


def get_dropdown_options():
    game_data = pd.read_csv("./configs/game_data.csv")
    choices = game_data["name"].astype(str).values.tolist()
    return choices


with gr.Blocks(theme=gr.themes.Soft(), title="💰代儲小助手", analytics_enabled=True) as demo:
    title = gr.Markdown("# 💰代儲小助手")
    with gr.Tab("價格查詢"):
        with gr.Row():
            app_id_input = gr.Dropdown(label="選擇 APP 📱", choices=get_dropdown_options())
            search_button = gr.Button("搜尋")

        with gr.Row():
            output_dataframe = gr.DataFrame(interactive=False)
            with gr.Column():
                selected_game = gr.Textbox(
                    label="你選擇的是: ", placeholder="請點選上方任意行選擇要儲存的遊戲..."
                )
                user_selected_block = gr.Textbox(visible=False)
                save_button = gr.Button("查詢價格")
        game_info_data = gr.DataFrame(interactive=False)
        with gr.Row():
            icon_url = gr.Image(height=256, width=256, show_label=False, visible=False)
            selected_game_screenshots = gr.Gallery(columns=[3], rows=[3], label="遊戲截圖")

        save_result = gr.Markdown()
        selected_game_data = gr.DataFrame(visible=False)

        search_button.click(fn=update_output, inputs=app_id_input, outputs=output_dataframe)
        output_dataframe.select(
            get_user_selected_row,
            inputs=[output_dataframe],
            outputs=[
                selected_game_data,
                selected_game,
                user_selected_block,
                icon_url,
                selected_game_screenshots,
            ],
        )
        save_button.click(
            fn=save_data, inputs=[selected_game_data], outputs=[save_result, game_info_data]
        )

demo.launch(
    share=False,
    server_name="0.0.0.0",
    server_port=7860,
    show_api=False,
    debug=True,
    # auth_message=auth_message,
    # auth=auth,
    # root_path="/seller",
)
