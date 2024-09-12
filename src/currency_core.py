import bs4
import logfire
from pydantic import Field, BaseModel, computed_field
import requests

from models.currency_rate import CurrencyInfo, CurrencyRate

logfire.configure()


class CurrencyCore(BaseModel):
    country_name: str = Field(default="usd", title="Country Name", description="Country name")

    @computed_field
    @property
    def base_url(self) -> str:
        return f"https://www.twrates.com/card/mastercard/{self.country_name}.html"

    @staticmethod
    def __parse_exchange_rate_info(exchange_rate_info: str) -> CurrencyInfo:
        if "(" in exchange_rate_info:
            exchange_rate, date_info = exchange_rate_info.split("(")
            date_info = date_info.rstrip(")").strip()
        else:
            exchange_rate, date_info = exchange_rate_info, ""
        exchange_rate = exchange_rate.replace("\xa0", "").strip()
        return CurrencyInfo(exchange_rate=exchange_rate, date_info=date_info)

    def get_all_currency(self) -> list[dict[str, str]]:
        """Retrieves a list of all available currencies and their corresponding links.

        Returns:
            A list of dictionaries, where each dictionary contains the currency name (in Chinese) as the key and the currency link as the value.

        Example:
            >>> currency_rate = CurrencyCore(country_name="usd")
            >>> all_currency = currency_rate.get_all_currency()[0]
            >>> print(all_currency)
            {'美金': 'https://www.twrates.com/card/mastercard/usd.html'}
        """
        # Use this as base url to get all available currency
        response = requests.get(self.base_url)
        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            __currency_list: bs4.element.Tag = soup.find_all("li", class_="itm")
            currency_list = []
            for currency in __currency_list:
                currency_name = currency.text.strip()
                currency_name_cn = currency_name.split(" - ")[-1]
                _currency_link = currency.find("a")["href"]
                currency_link = f"https://www.twrates.com{_currency_link}"
                currency_list.append({currency_name_cn: currency_link})
        else:
            logfire.exception("Failed to get currency list", url=self.base_url)
        return currency_list

    def fetch_currency_rates(self) -> CurrencyRate:
        """Fetches the currency rates for a specific country.

        Returns:
            CurrencyRate: An object containing the currency rates.

        Raises:
            logfire.exception: If the request to fetch the currency rates fails.

        Example:
            >>> currency_rate = CurrencyCore(country_name="usd")
            >>> result = currency_rate.fetch_currency_rates()
            >>> print(result.model_dump())
            {'currency_en': 'usd', 'currency_cn': '美金', 'jcb': '32.137', 'master': '32.189', 'visa': '32.169', 'updated_time': '2024-09-12'}
        """
        response = requests.get(self.base_url)
        if response.status_code != 200:
            raise logfire.exception("Failed to get currency rates.", url=self.base_url)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        rows: list[bs4.element.Tag] = soup.find_all("tr")
        currency_content = soup.find("a", onclick="change_ccy()")
        currency_name = "未找到幣值名稱"
        if currency_content:
            currency_name = (
                currency_content.text.split(" - ")[1]
                .split("&nbsp;&nbsp;")[0]
                .replace("\xa0", "")
                .strip()
            )
        result = {"currency_en": self.country_name, "currency_cn": currency_name}
        for row in rows:
            _cols = row.find_all("td")
            if len(_cols) > 1:
                card_type: str = _cols[0].text.strip()
                exchange_rate_info: str = _cols[1].text.strip()
                currency_info = self.__parse_exchange_rate_info(exchange_rate_info)
                result[card_type] = currency_info.exchange_rate
        result["updated_time"] = currency_info.date_info
        return CurrencyRate(**result)


if __name__ == "__main__":
    currency_rate = CurrencyCore(country_name="usd")
    currency_rate.fetch_currency_rates()
    currency_rate.get_all_currency()
