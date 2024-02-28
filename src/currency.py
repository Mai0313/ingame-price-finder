import os

from bs4 import BeautifulSoup
import pandas as pd
from pydantic import Field, BaseModel
import requests
from rich.console import Console

console = Console()


class CurrencyRate(BaseModel):
    country_name: str = Field(..., title="Country Name", description="Country name")

    @staticmethod
    def parse_exchange_rate_info(exchange_rate_info: str) -> tuple[str, str]:
        if "(" in exchange_rate_info:
            exchange_rate, date_info = exchange_rate_info.split("(")
            date_info = date_info.replace(")", "").strip()
        else:
            exchange_rate = exchange_rate_info
            date_info = ""
        return exchange_rate, date_info

    def parse_currency_rates(self, html_content: str):
        soup = BeautifulSoup(html_content, "html.parser")
        rows = soup.find_all("tr")
        currency_content = soup.find("a", onclick="change_ccy()")
        country_rates = {}
        currency_name = "未找到幣值名稱"
        if currency_content:
            currency_name = (
                currency_content.text.split(" - ")[1]
                .split("&nbsp;&nbsp;")[0]
                .replace("\xa0", "")
                .strip()
            )

        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 1:
                card_type = cols[0].text.strip()
                exchange_rate_info = cols[1].text.strip()
                exchange_rate, date_info = self.parse_exchange_rate_info(exchange_rate_info)
                exchange_rate = exchange_rate.replace("\xa0", "").strip()

                if self.country_name not in country_rates:
                    country_rates[self.country_name] = {
                        "Currency": self.country_name,
                        "Currency_CN": currency_name,
                        "Updated_date": date_info,
                        "JCB": None,
                        "萬事達": None,
                        "VISA": None,
                    }
                country_rates[self.country_name][card_type] = exchange_rate

        return country_rates.values()

    def fetch_currency_rates(self):
        url = f"https://www.twrates.com/card/mastercard/{self.country_name}.html"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = self.parse_currency_rates(response.text)
            return result
        except Exception as e:
            pass


class DataParser(BaseModel):
    path: str = Field(..., title="Path", description="Path to the file")
    output_path: str = Field(...)

    @staticmethod
    def __combine_currency_rates(
        original_data: pd.DataFrame, currency_results: pd.DataFrame
    ) -> pd.DataFrame:
        combined_data = pd.merge(
            currency_results, original_data, left_on="Currency", right_on="Code", how="right"
        )
        combined_data = combined_data[
            [
                "Country",
                "CountryCode",
                "Currency",
                "Currency_CN",
                "Updated_date",
                "JCB",
                "萬事達",
                "VISA",
            ]
        ]
        combined_data = combined_data.drop_duplicates(subset="Country")
        return combined_data

    def get_country_code_dict(self):
        original_data = pd.read_csv(self.path)[["Country", "Code", "CountryCode"]]
        country_code_dict = {}
        for index, row in original_data.iterrows():
            # 排除重複幣值 因為有些國家是用相同幣值
            if row["Code"] not in country_code_dict.values():
                country_code_dict[row["Country"]] = row["Code"]

        currency_results = pd.DataFrame()
        for country_name, country_code in country_code_dict.items():
            currency_rate = CurrencyRate(country_name=country_code)
            currency_result = currency_rate.fetch_currency_rates()
            currency_result = pd.DataFrame.from_dict(currency_result)
            currency_results = pd.concat([currency_results, currency_result])

        output_path_dir = os.path.dirname(self.output_path)
        os.makedirs(output_path_dir, exist_ok=True)
        currency_results = self.__combine_currency_rates(original_data, currency_results)
        currency_results.to_csv(f"./{self.output_path}", index=False)


if __name__ == "__main__":
    data_parser = DataParser(
        path="./configs/countries_currency.csv", output_path="./data/currency_rates.csv"
    )
    result = data_parser.get_country_code_dict()
