from pydantic import Field, BaseModel


class GameInfo(BaseModel):
    game_id: str = Field(
        ...,
        title="Package ID",
        description="Package ID from play store",
        alias="packageId",
        examples=["com.ncsoft.lineagew"],
        deprecated=False,
    )
    game_name: str = Field(
        ...,
        title="Game Name",
        description="Game Name from play store",
        alias="name",
        examples=["天堂W"],
        deprecated=False,
    )


class GamePriceInfo(BaseModel):
    name: str | None
    country: str
    lowest: float
    highest: float
