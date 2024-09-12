from pydantic import Field, BaseModel


class GameInfoModel(BaseModel):
    game_id: str = Field(..., title="Package ID", alias="packageId")
    game_name: str = Field(..., title="Game Name", alias="name")
