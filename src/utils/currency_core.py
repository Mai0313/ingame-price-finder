from bs4 import BeautifulSoup
from pydantic import Field, BaseModel
import requests


class CurrencyCore(BaseModel):
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
