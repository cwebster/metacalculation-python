from pydantic import BaseModel, Field
from typing import Optional

class UncertaintyResult(BaseModel):
    N: int
    # We use alias to preserve the original "W.Median" key
    W_Median: Optional[float] = Field(None, alias="W.Median")
    Range_lower: Optional[float] = Field(None, alias="Range_lower")
    Range_upper: Optional[float] = Field(None, alias="Range_upper")

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "N": 5,
                "W.Median": 0.123,
                "Range_lower": 0.10,
                "Range_upper": 0.15
            }
        }
