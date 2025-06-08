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
async def test_compare_many_random_datasets_with_summary():
    headers = {"Content-Type": "text/plain"}
    total = 1000
    failures = []
    for i in range(total):
        n = random.randint(1, 20)
        CSV_DATA = make_csv(n)
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
                if local_val != biovar_val:
                    failures.append(f"#{i} {key}: {local_val} != {biovar_val} (n={n})")
            else:
                if not math.isclose(local_val, biovar_val, rel_tol=1e-2, abs_tol=0.02):
                    failures.append(f"#{i} {key}: {local_val} != {biovar_val} (n={n})")

        local_n = extract_scalar(local_json.get("N"))
        biovar_n = extract_scalar(biovar_json.get("N"))
        if local_n != biovar_n:
            failures.append(f"#{i} N: {local_n} != {biovar_n} (n={n})")

    print(f"\nRandomized test summary: {total - len(failures)} passed, {len(failures)} failed.")
    if failures:
        print("Failures:")
        for fail in failures:
            print(fail)
    assert not failures, f"{len(failures)} failures out of {total} tests."