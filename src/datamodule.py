from typing import Optional
import sqlite3
import datetime

import pandas as pd
from pydantic import Field, BaseModel, ConfigDict, computed_field
from src.currency import CurrencyRate
from src.ingame_price import GameInfo


class DataBaseManager(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database_name: str = Field(...)

    @computed_field
    @property
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_name)
        return conn

    @computed_field
    @property
    def table_names(self) -> list[str]:
        try:
            table_names_ = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table';", self.get_connection
            )
            table_names_ = table_names_["name"].values.tolist()
            return table_names_
        except Exception:
            return []

    def save_table(
        self, table_name: str, data: pd.DataFrame, mode: Optional[str] = "replace"
    ) -> pd.DataFrame:
        if not data.empty:
            data.to_sql(f"{table_name}", self.get_connection, index=False, if_exists=mode)
        return data

    def read_table(self, table_name: str) -> pd.DataFrame:
        data = pd.read_sql_query(f"SELECT * FROM '{table_name}'", self.get_connection)
        return data

    @computed_field
    @property
    def currency_rate(self) -> pd.DataFrame:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "currency_rates" in self.table_names:
            data = self.read_table("currency_rates")
            updated_time = data["database_updated_date"].values[0]
            if pd.to_datetime(now) - pd.to_datetime(updated_time) < pd.Timedelta(days=3):
                return data
            else:
                currency_rate = CurrencyRate(path="./configs/countries_currency.csv")
                currency_rate = currency_rate.get_country_currency()
                currency_rate["database_updated_date"] = now
                self.save_table("currency_rates", currency_rate)
                # Save for pytest or dev purposes
                currency_rate.to_csv("./data/currency_rates.csv", index=False)
                return currency_rate
        else:
            currency_rate = CurrencyRate(path="./configs/countries_currency.csv")
            currency_rate = currency_rate.get_country_currency()
            currency_rate["database_updated_date"] = now
            self.save_table("currency_rates", currency_rate)
            # Save for pytest or dev purposes
            currency_rate.to_csv("./data/currency_rates.csv", index=False)
            return currency_rate

    def update_ingame_price(
        self, table_name: str, target_game_id: Optional[str] = None
    ) -> pd.DataFrame:
        """這裡的table name可以是遊戲名稱 或是 任何名稱"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if table_name in self.table_names:
            data = self.read_table(table_name)
            updated_time = data["database_updated_date"].values[0]
            # 如果資料在三天內就不更新
            if pd.to_datetime(now) - pd.to_datetime(updated_time) < pd.Timedelta(days=3):
                return data
            else:
                game_info_instance = GameInfo(
                    target_game=table_name, target_game_id=target_game_id
                )
                game_info_data = game_info_instance.fetch_data(country_currency=self.currency_rate)
                game_info_data["database_updated_date"] = now
                self.save_table(table_name=table_name, data=game_info_data)
                return game_info_data
        else:
            game_info_instance = GameInfo(target_game=table_name, target_game_id=target_game_id)
            game_info_data = game_info_instance.fetch_data(country_currency=self.currency_rate)
            game_info_data["database_updated_date"] = now
            self.save_table(table_name=table_name, data=game_info_data)
            return game_info_data


if __name__ == "__main__":
    table_name = "原神"
    database_name = "./data/ingame_price.db"
    db_manager = DataBaseManager(database_name=database_name)
    data = db_manager.update_ingame_price(table_name=table_name)
