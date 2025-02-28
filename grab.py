import requests
from bs4 import BeautifulSoup
import pycountry
from rich.console import Console

console = Console()

countries = list(pycountry.countries.alpha_2)
console.print(countries)

# 目標網站的 URL
url = "https://app.sensortower.com/overview/985746746"

# 發送GET請求
response = requests.get(url)

# 確保網頁成功載入
if response.status_code == 200:
    # 解析 HTML
    soup = BeautifulSoup(response.content, 'html.parser')

    # 抓取option的部分，這裡假設有一個<select>標籤包含所有的選項
    options = soup.find_all('li', {'role': 'option'})
    
    # 儲存結果的清單
    countries = []

    # 遍歷所有的選項並抓取value與名稱
    for option in options:
        country_code = option['value']
        country_name = option.get_text()
        countries.append((country_name, country_code))

    # 顯示結果
    for country in countries:
        console.print(f"Country: {country[0]}, Code: {country[1]}")

else:
    console.print(f"Failed to retrieve the page, status code: {response.status_code}")
