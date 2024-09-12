import pandas as pd
from pydantic import Field, BaseModel

from src.currency_core import CurrencyCore


class CurrencyRate(BaseModel):
    path: str = Field(..., title="Path", description="Path to the file")

    @staticmethod
    def __combine_currency_rates(
        original_data: pd.DataFrame, currency_results: pd.DataFrame
    ) -> pd.DataFrame:
        combined_data = currency_results.merge(
            original_data, left_on="Currency", right_on="Code", how="right"
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

    def get_country_currency(self) -> pd.DataFrame:
        original_data = pd.read_csv(self.path)[["Country", "Code", "CountryCode"]]
        country_code_dict = {}
        for _, row in original_data.iterrows():
            # 排除重複幣值 因為有些國家是用相同幣值
            if row["Code"] not in country_code_dict.values():
                country_code_dict[row["Country"]] = row["Code"]

        currency_results = pd.DataFrame()
        for country_code in country_code_dict.values():
            currency_rate = CurrencyCore(country_name=country_code)
            currency_result = currency_rate.fetch_currency_rates()
            currency_result = pd.DataFrame.from_dict(currency_result)
            currency_results = pd.concat([currency_results, currency_result])

        currency_results = self.__combine_currency_rates(original_data, currency_results)
        # currency_results = currency_results.dropna(subset=["Currency"])
        return currency_results


if __name__ == "__main__":
    country_currencies = CurrencyRate(path="./configs/countries_currency.csv")
    country_currencies = country_currencies.get_country_currency()
    country_currencies.to_csv("./data/currency_rates.csv", index=False)
