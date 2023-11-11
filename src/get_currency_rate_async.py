import asyncio
import os
import re

import orjson
import pandas as pd
from omegaconf import OmegaConf
from playwright.async_api import async_playwright
from pydantic import BaseModel
from rich.progress import Progress
from rich.text import Text


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


class CurrencyRate(BaseModel):
    target_country: dict
    output_path: str

    async def get_default_country(self):
        os.makedirs(self.output_path, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, timeout=3000)
            page = await browser.new_page()

            result = []
            result_csv = []

            with Progress() as progress:
                task1 = progress.add_task("[cyan]Processing...", total=len(self.target_country))

                for i, (country, country_in_chinese) in enumerate(self.target_country.items()):
                    func_num = i + 2
                    target_url = f"https://www.bestxrate.com/card/mastercard/{country}.html"

                    try:
                        await page.goto(target_url, timeout=3000)
                        visa = await page.locator("#comparison_huilv_Visa").text_content(
                            timeout=3000
                        )
                        master_info = await page.locator(
                            ".odd:nth-child(1) > td:nth-child(2)"
                        ).text_content(timeout=3000)
                        master = get_date(master_info)
                        master, update_date = master.split("\xa0")
                        jcb = await page.locator("#comparison_huilv_JCB").text_content(
                            timeout=3000
                        )
                        data = {
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
                        result.append(data)
                        data_csv = {
                            "Country": country_in_chinese,
                            "Currency": country,
                            "Visa Currency": visa,
                            "Master Currency": master,
                            "JCB Currency": jcb,
                            "Update Time": update_date,
                        }
                        result_csv.append(data_csv)
                    except Exception as e:
                        print(
                            f"{country_in_chinese} has an error, please check {target_url} \n {e}"
                        )

                    progress.update(
                        task1,
                        completed=i + 1,
                        description=Text(f"[cyan]Processing {country} {country_in_chinese}"),
                    )

            result = pd.DataFrame(result)
            result_csv = pd.DataFrame(result_csv)
            result.to_excel(f"{self.output_path}/currency_rate.xlsx", index=False)
            result_csv.to_csv(f"{self.output_path}/currency_rate.csv", index=False)
            await browser.close()
            return result


if __name__ == "__main__":
    countries = get_country_list()
    config = OmegaConf.load("./configs/setting.yaml")
    output_path = config.config_path.currency_rate_output_path

    async def main():
        currency_rate = CurrencyRate(target_country=countries, output_path=output_path)
        await currency_rate.get_default_country()

    asyncio.run(main())
