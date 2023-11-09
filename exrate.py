import os

import orjson
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def get_country_list():
    with open('./configs/countries_original.json', 'rb') as file:
        json_data = file.read()
        data = orjson.loads(json_data)
    return data


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    WINDOW_SIZE = "1920,1080"
    options.add_argument("--window-size=%s" % WINDOW_SIZE)
    driver = webdriver.Chrome(options=options)
    return driver


def get_default_country(target_country, output_path):
    os.makedirs(output_path, exist_ok=True)
    result = pd.DataFrame()
    driver = get_driver()
    for i, (country, country_in_chinese) in enumerate(target_country.items()):
        func_num = i + 2
        driver.get(f"https://www.bestxrate.com/card/mastercard/{country}.html")
        try:
            visa = driver.find_element(By.ID, "comparison_huilv_Visa").text
            visadate = driver.find_element(By.CSS_SELECTOR, ".even .gray_font").text
            visadate = visadate.replace("(", "").replace(")", "")
            master = driver.find_element(By.CSS_SELECTOR, ".odd:nth-child(1) > td:nth-child(2)").text
            masterdate = master.split(" ")[-1].replace("(", "").replace(")", "")
            master = master.split(" ")[0]
            jcb = driver.find_element(By.CSS_SELECTOR, ".odd:nth-child(3) > td:nth-child(2)").text
            jcbdate = jcb.split(" ")[-1].replace("(", "").replace(")", "")
            jcb = jcb.split(" ")[0]
        except NoSuchElementException:
            pass
        data = [{
            "國家": country_in_chinese,
            "幣值": country,
            "金額": 2990,
            "更新時間": visadate,
            "Visa匯率": visa,
            "Visa 試算結果": f"=C{func_num}*E{func_num}*1.5",
            "Master匯率": master,
            "Master 試算結果": f"=C{func_num}*H{func_num}*1.5",
            "JCB匯率": jcb,
            "JCB 試算結果": f"=C{func_num}*K{func_num}*1.5",
        }]
        data = pd.DataFrame(data)
        result = pd.concat([result, data], axis=0, ignore_index=True)
        print(country_in_chinese, "has been done")
    result.to_excel(f"{output_path}/即時匯率.xlsx", index=False)
    return result


if __name__ == "__main__":
    countries = get_country_list()
    output_path = "data"
    get_default_country(countries, output_path)
