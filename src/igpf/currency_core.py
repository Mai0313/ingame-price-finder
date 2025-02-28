import bs4
import logfire
from pydantic import BaseModel
import requests
from _types.currency_rate import CurrencyInfo, CurrencyRate, CountryCurrency

logfire.configure()


class CurrencyCore(BaseModel):
    def get_country_list(self) -> list[CountryCurrency]:
        """Retrieves a list of all available currencies and their corresponding links.

        Returns:
            A list of dictionaries, where each dictionary contains the currency name (in Chinese) as the key and the currency link as the value.

        Example:
            >>> currency_rate = CurrencyCore()
            >>> all_currency = currency_rate.get_country_list()
            >>> print(all_currency[0])
            CountryCurrency(currency_name='usd', currency_name_cn='美金', currency_url='https://www.twrates.com/card/mastercard/usd.html')
        """
        # Use this as base url to get all available currency
        base_url = "https://www.twrates.com/card/mastercard/usd.html"
        response = requests.get(url=base_url)
        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            currency_result: list[bs4.element.Tag] = soup.find_all("li", class_="itm")
            currency_list = []
            for currency in currency_result:
                if not isinstance(currency.text, str):
                    continue
                currency_name = currency.text.strip()
                currency_name_en = currency_name.split(" - ")[0].lower()
                currency_name_cn = currency_name.split(" - ")[-1]
                _currency_link = currency.find("a")["href"]
                currency_link = f"https://www.twrates.com{_currency_link}"
                country_currency = CountryCurrency(
                    currency_name=currency_name_en,
                    currency_name_cn=currency_name_cn,
                    currency_url=currency_link,
                )
                currency_list.append(country_currency)
            return currency_list
        logfire.exception("Failed to get currency list", url=base_url)
        raise ValueError("Failed to get currency list")

    @staticmethod
    def __parse_exchange_rate_info(exchange_rate_info: str) -> CurrencyInfo:
        if "(" in exchange_rate_info:
            exchange_rate, date_info = exchange_rate_info.split("(")
            date_info = date_info.rstrip(")").strip()
        else:
            exchange_rate, date_info = exchange_rate_info, ""
        exchange_rate = exchange_rate.replace("\xa0", "").strip()
        return CurrencyInfo(exchange_rate=exchange_rate, date_info=date_info)

    def _get_currency_rate(self, country_name: str) -> CurrencyRate:
        """Fetches the currency rates for a specific country.

        Returns:
            CurrencyRate: An object containing the currency rates.

        Raises:
            logfire.exception: If the request to fetch the currency rates fails.

        Example:
            >>> currency_rate = CurrencyCore()
            >>> result = currency_rate.fetch_currency_rates(country_name="usd")
            >>> print(result.model_dump())
            {'currency_en': 'usd', 'currency_cn': '美金', 'jcb': '32.137', 'master': '32.189', 'visa': '32.169', 'updated_time': '2024-09-12'}
        """
        base_url = f"https://www.twrates.com/card/mastercard/{country_name}.html"
        response = requests.get(base_url)
        if response.status_code != 200:
            logfire.exception("Failed to get currency rates.", url=base_url)
            raise ValueError("Failed to get currency rates.")
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        rows: list[bs4.element.Tag] = soup.find_all("tr")
        currency_content = soup.find("a", onclick="change_ccy()")
        currency_name = "未找到幣值名稱"
        if not isinstance(currency_content.text, str):
            raise logfire.exception("Failed to get currency name")
        if currency_content:
            currency_name = (
                currency_content.text.split(" - ")[1]
                .split("&nbsp;&nbsp;")[0]
                .replace("\xa0", "")
                .strip()
            )
        result = {"currency_en": country_name, "currency_cn": currency_name}
        for row in rows:
            cols: list[bs4.element.Tag] = row.find_all("td")
            if len(cols) > 1:
                card_type: str = cols[0].text.strip()
                exchange_rate_info: str = cols[1].text.strip()
                currency_info = self.__parse_exchange_rate_info(exchange_rate_info)
                result[card_type] = currency_info.exchange_rate
        result["updated_time"] = currency_info.date_info
        logfire.info("Currency rate fetched successfully.", url=base_url, **result)
        return CurrencyRate(**result)

    def fetch_currency_rates(self, currency_name_en: str) -> list[CurrencyRate]:
        currency_rate_list = []
        if currency_name_en == "all":
            country_list = self.get_country_list()
            for currency_dict in country_list:
                fetched_currency = self._get_currency_rate(
                    country_name=currency_dict.currency_name
                )
                currency_rate_list.append(fetched_currency)
        else:
            fetched_currency = self._get_currency_rate(country_name=currency_name_en)
            currency_rate_list.append(fetched_currency)
        return currency_rate_list


if __name__ == "__main__":
    currency_rate = CurrencyCore()
    currency_rate.fetch_currency_rates(currency_name_en="all")
