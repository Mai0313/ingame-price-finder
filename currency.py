from bs4 import BeautifulSoup
import pandas as pd
from pydantic import Field, BaseModel
import requests


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
        country_rates = {}

        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 1:
                card_type = cols[0].text.strip()
                exchange_rate_info = cols[1].text.strip()
                exchange_rate, date_info = self.parse_exchange_rate_info(exchange_rate_info)
                exchange_rate = exchange_rate.replace("\xa0", "").strip()

                if self.country_name not in country_rates:
                    country_rates[self.country_name] = {
                        "currency": self.country_name,
                        "更新日期": date_info,
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
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")  # noqa: T201
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")  # noqa: T201
        return result


class DataParser(BaseModel):
    path: str = Field(..., title="Path", description="Path to the file")

    def get_country_code_dict(self):
        data = pd.read_csv(self.path)
        country_code_dict = {}
        for index, row in data.iterrows():
            country_code_dict[row["Country"]] = row["Code"]

        final_result = pd.DataFrame()
        for country_name, country_code in country_code_dict.items():
            currency_rate = CurrencyRate(country_name=country_code)
            result = currency_rate.fetch_currency_rates()
            result = pd.DataFrame.from_dict(result)
            final_result = pd.concat([final_result, result])


if __name__ == "__main__":
    data_parser = DataParser(path="./configs/countries_currency.csv")
    data_parser.get_country_code_dict()
