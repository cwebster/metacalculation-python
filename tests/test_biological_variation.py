import pytest
import httpx
import random
import math

LOCAL_API_URL = "http://localhost:8081/metacalculation"
BIOVAR_API_URL = "https://r.biologicalvariation.eu/metacalculation"

def make_csv(n):
    rows = [
        f"{i+1},TRUE,C,{round(random.uniform(10, 30), 2)},{round(random.uniform(5, 20), 3)},{round(random.uniform(20, 40), 3)}"
        for i in range(n)
    ]
    header = "ID,Include,Score,CV,CI_lower,CI_upper"
    return header + "\n" + "\n".join(rows) + "\n"

def extract_scalar(val):
    if isinstance(val, list):
        return val[0] if val else None
    return val

@pytest.mark.asyncio
@pytest.mark.parametrize("n", range(1, 16))
async def test_compare_all_with_biologicalvariation(n):
    CSV_DATA = make_csv(n)
    headers = {"Content-Type": "text/plain"}
    async with httpx.AsyncClient() as client:
        local_resp = await client.post(LOCAL_API_URL, content=CSV_DATA, headers=headers)
        assert local_resp.status_code == 200
        local_json = local_resp.json()

        biovar_resp = await client.post(BIOVAR_API_URL, content=CSV_DATA, headers=headers)
        assert biovar_resp.status_code == 200
        biovar_json = biovar_resp.json()

    for key in ["W.Median", "Range_lower", "Range_upper"]:
        local_val = extract_scalar(local_json.get(key))
        biovar_val = extract_scalar(biovar_json.get(key))
        if local_val is None or biovar_val is None:
            assert local_val == biovar_val, f"{key}: {local_val} != {biovar_val} (n={n})"
        else:
            assert math.isclose(local_val, biovar_val, rel_tol=1e-2, abs_tol=0.02), f"{key}: {local_val} != {biovar_val} (n={n})"

    local_n = extract_scalar(local_json.get("N"))
    biovar_n = extract_scalar(biovar_json.get("N"))
    assert local_n == biovar_n, f"N: {local_n} != {biovar_n} (n={n})"