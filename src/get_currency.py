import requests
import logfire
from bs4.element import Tag
from bs4 import BeautifulSoup

def get_all_currency():
    url = 'https://www.twrates.com/card/mastercard/usd.html'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        __currency_list: Tag = soup.find_all('li', class_='itm')
        currency_list = []
        for currency in __currency_list:
            currency_name = currency.text.strip()
            currency_name_cn = currency_name.split(" - ")[-1]
            currency_link = currency.find('a')['href']
            result_dict = {currency_name_cn: currency_link}
            currency_list.append(result_dict)
    else:
        logfire.error(f"Failed to get currency list from {url}")
    return currency_list
