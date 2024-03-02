import pandas as pd
from pydantic import Field, BaseModel, ConfigDict


class PriceDetails(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    country_currency: pd.DataFrame = Field(...)
    game_info: pd.DataFrame = Field(...)

    def get_price_details(self):
        price_details = pd.merge(
            self.country_currency,
            self.game_info,
            left_on="CountryCode",
            right_on="country",
            how="left",
        )
        price_details = price_details[
            [
                "Name",
                "country",
                "CountryCode",
                "Currency",
                "Currency_CN",
                "Updated_date",
                "lowest",
                "highest",
                "JCB",
                "萬事達",
                "VISA",
            ]
        ]

        price_details["JCB 最高價"] = price_details["JCB"] * price_details["highest"]
        price_details["萬事達 最高價"] = price_details["萬事達"] * price_details["highest"]
        price_details["VISA 最高價"] = price_details["VISA"] * price_details["highest"]

        price_details["JCB 最低價"] = price_details["JCB"] * price_details["lowest"]
        price_details["萬事達 最低價"] = price_details["萬事達"] * price_details["lowest"]
        price_details["VISA 最低價"] = price_details["VISA"] * price_details["lowest"]

        price_details = price_details.drop(["JCB", "萬事達", "VISA", "country"], axis=1)
        price_details = price_details.drop_duplicates()
        price_details = price_details.dropna(
            subset=[
                "Name",
                "JCB 最高價",
                "萬事達 最高價",
                "VISA 最高價",
                "JCB 最低價",
                "萬事達 最低價",
                "VISA 最低價",
            ],
            how="any",
        )
        return price_details


if __name__ == "__main__":
    import autorootcwd

    country_currency = pd.read_csv("./data/currency_rates.csv")
    game_info = pd.read_csv("./data/原神.csv")
    result = PriceDetails(
        country_currency=country_currency, game_info=game_info
    ).get_price_details()
    result.to_csv("./data/price_details.csv", index=False)
