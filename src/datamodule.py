import pandas as pd
from pydantic import Field, BaseModel


class PriceDetails(BaseModel):
    country_currency: str = Field(...)
    game_info: str = Field(...)

    def get_price_details(self):
        country_currency = pd.read_csv(self.country_currency)
        game_info = pd.read_csv(self.game_info)
        price_details = pd.merge(
            country_currency, game_info, left_on="CountryCode", right_on="country", how="left"
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

        price_details["JCB"] = price_details["JCB"] * price_details["highest"]
        price_details["萬事達"] = price_details["萬事達"] * price_details["highest"]
        price_details["VISA"] = price_details["VISA"] * price_details["highest"]
        return price_details
