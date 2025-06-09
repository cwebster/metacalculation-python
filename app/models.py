from pydantic import BaseModel, Field, RootModel
from typing import Optional, List

class UncertaintyResult(BaseModel):
    N: int
    W_Median: Optional[float] = Field(None, alias="W.Median")
    Range_lower: Optional[float] = Field(None, alias="Range_lower")
    Range_upper: Optional[float] = Field(None, alias="Range_upper")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "N": 5,
                "W.Median": 0.123,
                "Range_lower": 0.10,
                "Range_upper": 0.15
            }
        }
    }

class MetacalculationInputRow(BaseModel):
    ID: int
    Include: bool
    Score: str
    CV: float
    CI_lower: float
    CI_upper: float

class MetacalculationInput(RootModel[list[MetacalculationInputRow]]):
    pass
