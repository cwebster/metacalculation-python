# Metacalculation Service (FastAPI)
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

## Building

```bash
docker build -t metacalculation-service .
```

## Running

```bash
docker run -p 8080:8080 metacalculation-service
```

- **Health check**: `GET /health`  
- **Meta calculation**: `POST /metacalculation`  
  - **Body** (`text/plain`): CSV with columns  
    `ID, CV, CI_lower, CI_upper, Score, Include`  
  - **Response**: JSON with  
    ```
    {
      "N": <int>,
      "W.Median": <float|null>,
      "Range_lower": <float|null>,
      "Range_upper": <float|null>
    }
    ```
