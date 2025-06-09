from fastapi import FastAPI, HTTPException, Request
from app.models import UncertaintyResult, MetacalculationInput
from app.core import trunc_testdata, calc_median_uncertainty
import pandas as pd

app = FastAPI()

@app.get("/health")
def health():
    return "OK"

@app.post(
    "/metacalculation",
    response_model=UncertaintyResult,
    description="""
This endpoint accepts input data in either **JSON** or **CSV** format.

- **JSON:** Set `Content-Type: application/json` and provide a JSON array of objects matching the schema.
- **CSV:** Set `Content-Type: text/csv` or `text/plain` and provide CSV text with columns: `ID,Include,Score,CV,CI_lower,CI_upper`.

Example JSON:
```json
[
  {"ID": 1, "Include": true, "Score": "C", "CV": 18.8, "CI_lower": 14.648, "CI_upper": 25.564},
  {"ID": 2, "Include": true, "Score": "C", "CV": 20.1, "CI_lower": 15.0, "CI_upper": 27.0}
]
```

Example CSV:
```
ID,Include,Score,CV,CI_lower,CI_upper
1,TRUE,C,18.8,14.648,25.564
2,TRUE,C,20.1,15.000,27.000
```
"""
)
async def metacalculation(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
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
