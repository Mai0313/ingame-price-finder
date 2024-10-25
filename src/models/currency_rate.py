from pydantic import Field, BaseModel


class CurrencyRate(BaseModel):
    currency_en: str = Field(..., title="Currency Name", description="Currency name")
    currency_cn: str = Field(
        ..., title="Currency Name (Chinese)", description="Currency name in Chinese"
    )
    jcb: str | None = Field(default=None, alias="JCB")
    master: str | None = Field(default=None, alias="萬事達")
    visa: str | None = Field(default=None, alias="VISA")
    updated_time: str = Field(..., title="Updated Time", description="Updated time")


class CurrencyInfo(BaseModel):
    exchange_rate: str = Field(..., title="Exchange Rate", description="Exchange rate")
    date_info: str = Field(..., title="Date Info", description="Date info")
