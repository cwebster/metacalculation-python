# compare_performance.py
import httpx
import time
import statistics

PY_URL = "https://py.biologicalvariation.eu/metacalculation"
R_URL = "https://r.biologicalvariation.eu/metacalculation"

csv_data = """ID,Include,Score,CV,CI_lower,CI_upper
1,TRUE,C,18.8,14.648,25.564
2,TRUE,C,20.1,15.000,27.000
"""

json_data = [
    {"ID": 1, "Include": True, "Score": "C", "CV": 18.8, "CI_lower": 14.648, "CI_upper": 25.564},
    {"ID": 2, "Include": True, "Score": "C", "CV": 20.1, "CI_lower": 15.0, "CI_upper": 27.0}
]

def print_stats(times, label):
    avg = statistics.mean(times)
    stddev = statistics.stdev(times) if len(times) > 1 else 0.0
    cv = (stddev / avg * 100) if avg != 0 else 0.0
    print(f"{label} over {len(times)} runs:")
    print(f"  Mean: {avg:.4f} s")
    print(f"  Stddev: {stddev:.4f} s")
    print(f"  %CV: {cv:.2f}%\n")

def test_csv_endpoint(url, csv_payload, n=10):
    times = []
    for _ in range(n):
        start = time.perf_counter()
        response = httpx.post(url, content=csv_payload, headers={"Content-Type": "text/plain"})
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        assert response.status_code == 200, f"Failed: {url} {response.status_code}"
    print_stats(times, f"{url} (CSV)")

def test_json_endpoint(url, json_payload, n=10):
    times = []
    for _ in range(n):
        start = time.perf_counter()
        response = httpx.post(url, json=json_payload)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        assert response.status_code == 200, f"Failed: {url} {response.status_code}"
    print_stats(times, f"{url} (JSON)")

if __name__ == "__main__":
    # Test CSV on both endpoints and collect last responses
    print("Testing CSV on py endpoint...")
    py_times = []
    for _ in range(10):
        start = time.perf_counter()
        py_resp = httpx.post(PY_URL, content=csv_data, headers={"Content-Type": "text/plain"})
        elapsed = time.perf_counter() - start
        py_times.append(elapsed)
        assert py_resp.status_code == 200, f"Failed: {PY_URL} {py_resp.status_code}"
    print_stats(py_times, f"{PY_URL} (CSV)")

    print("Testing CSV on r endpoint...")
    r_times = []
    for _ in range(10):
        start = time.perf_counter()
        r_resp = httpx.post(R_URL, content=csv_data, headers={"Content-Type": "text/plain"})
        elapsed = time.perf_counter() - start
        r_times.append(elapsed)
        assert r_resp.status_code == 200, f"Failed: {R_URL} {r_resp.status_code}"
    print_stats(r_times, f"{R_URL} (CSV)")

    # Print and compare results
    print("py endpoint result (CSV):")
    print(py_resp.json())
    print("\nr endpoint result (CSV):")
    print(r_resp.json())

    if py_resp.json() == r_resp.json():
        print("\nResults match exactly.")
    else:
        print("\nResults differ.")

    # Test JSON on py endpoint and show result
    print("\nTesting JSON on py endpoint...")
    json_times = []
    for _ in range(10):
        start = time.perf_counter()
        py_json_resp = httpx.post(PY_URL, json=json_data)
        elapsed = time.perf_counter() - start
        json_times.append(elapsed)
        assert py_json_resp.status_code == 200, f"Failed: {PY_URL} {py_json_resp.status_code}"
    print_stats(json_times, f"{PY_URL} (JSON)")
    print("py endpoint result (JSON):")
    print(py_json_resp.json())