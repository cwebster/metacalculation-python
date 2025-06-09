from fastapi import FastAPI, HTTPException, Request
from app.models import UncertaintyResult, MetacalculationInput
from app.core import trunc_testdata, calc_median_uncertainty
import pandas as pd

app = FastAPI()

@app.get("/health")
def health():
    return "OK"

@app.post("/metacalculation", response_model=UncertaintyResult)
async def metacalculation(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            # Validate and parse JSON using Pydantic
            json_data = MetacalculationInput.model_validate(data)
            df = pd.DataFrame([row.model_dump() for row in json_data.root])
            df = trunc_testdata(df)
        elif "text/csv" in content_type or "text/plain" in content_type:
            body = await request.body()
            df = trunc_testdata(body.decode())
        else:
            raise HTTPException(status_code=415, detail="Unsupported Content-Type")
        return calc_median_uncertainty(df)
    except Exception as e:
        print("Error in /metacalculation:", e)
        raise HTTPException(status_code=400, detail=str(e))
