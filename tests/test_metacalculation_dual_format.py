from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_metacalculation_json_and_csv_equivalence():
    # Example data
    data = [
        {"ID": 1, "Include": True, "Score": "C", "CV": 18.8, "CI_lower": 14.648, "CI_upper": 25.564},
        {"ID": 2, "Include": True, "Score": "C", "CV": 20.1, "CI_lower": 15.000, "CI_upper": 27.000},
    ]
    csv_data = (
        "ID,Include,Score,CV,CI_lower,CI_upper\n"
        "1,TRUE,C,18.8,14.648,25.564\n"
        "2,TRUE,C,20.1,15.000,27.000\n"
    )

    # Submit as JSON
    resp_json = client.post(
        "/metacalculation",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print("JSON status:", resp_json.status_code)
    print("JSON response:", resp_json.json())
    assert resp_json.status_code == 200
    result_json = resp_json.json()

    # Submit as CSV
    resp_csv = client.post(
        "/metacalculation",
        content=csv_data,
        headers={"Content-Type": "text/plain"}
    )
    assert resp_csv.status_code == 200
    result_csv = resp_csv.json()

    # Results should be the same
    assert result_json == result_csv