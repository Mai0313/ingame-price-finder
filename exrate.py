import os
import re

import orjson
import pandas as pd
from playwright.sync_api import sync_playwright


def get_country_list():
    with open("./configs/countries_original.json", "rb") as file:
        json_data = file.read()
        data = orjson.loads(json_data)
    return data


def get_price(input_string):
    """This function will remove date from input string.

    Args:
        input_string (str): input string

    Returns:
        str: output string

    Examples:
        32.24400000 (2023-11-09) > 32.24400000
    """
    output_string = re.sub(r"\s*\([^)]*\)", "", input_string)
    return output_string


def get_date(input_string):
    """This function will remove () from input string.

    Args:
        input_string (str): input string

    Returns:
        output_string (str): output string

    Examples:
        (2023-11-09) > 2023-11-09
    """
    output_string = re.sub(r"[()]", "", input_string)
    return output_string


def get_default_country(browser, target_country, output_path):
    os.makedirs(output_path, exist_ok=True)
    page = browser.new_page()

    result = pd.DataFrame()
    result_csv = pd.DataFrame()
    for i, (country, country_in_chinese) in enumerate(target_country.items()):
        func_num = i + 2
        target_url = f"https://www.bestxrate.com/card/mastercard/{country}.html"
        page.goto(target_url, timeout=5000)

        try:
            visa = page.locator("#comparison_huilv_Visa").text_content()
            master_info = page.locator(".odd:nth-child(1) > td:nth-child(2)").text_content()
            master = get_date(master_info)
            master, update_date = master.split("\xa0")
            jcb = page.locator("#comparison_huilv_JCB").text_content()
            data = [
                {
                    "國家": country_in_chinese,
                    "幣值": country,
                    "金額": 2990,
                    "更新時間": update_date,
                    "Visa匯率": visa,
                    "Visa 試算結果": f"=C{func_num}*E{func_num}*1.5",
                    "Master匯率": master,
                    "Master 試算結果": f"=C{func_num}*H{func_num}*1.5",
                    "JCB匯率": jcb,
                    "JCB 試算結果": f"=C{func_num}*K{func_num}*1.5",
                }
            ]
            data = pd.DataFrame(data)
            result = pd.concat([result, data], axis=0, ignore_index=True)

            data_csv = [
                {
                    "國家": country_in_chinese,
                    "幣值": country,
                    "更新時間": update_date,
                    "Visa匯率": visa,
                    "Master匯率": master,
                    "JCB匯率": jcb,
                }
            ]
            data_csv = pd.DataFrame(data_csv)
            result_csv = pd.concat([result_csv, data_csv], axis=0, ignore_index=True)
            print(country_in_chinese, "has been done")
        except Exception as e:
            print(f"{country_in_chinese} has an error, please check {target_url}")
            continue

    result.to_excel(f"{output_path}/即時匯率.xlsx", index=False)
    browser.close()
    return result


if __name__ == "__main__":
    countries = get_country_list()
    output_path = "data"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        get_default_country(browser, countries, output_path)
