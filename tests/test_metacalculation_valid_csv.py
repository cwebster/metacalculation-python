import pytest
from fastapi.testclient import TestClient
from app.main import app
from typing import cast

# app/test_main.py


client = TestClient(app)

def test_metacalculation_valid_csv():
    csv_data = (
        "ID,Include,Score,CV,CI_lower,CI_upper\n"
        "4,TRUE,C,18.8,14.648,25.564\n"
        "5,TRUE,C,20.1,15.000,27.000\n"
    )

    response = client.post(
        "/metacalculation",
        content=csv_data,
        headers={"Content-Type": "text/plain"}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "N" in json_data
    assert "W.Median" in json_data
    assert "Range_lower" in json_data
    assert "Range_upper" in json_data
    assert json_data["N"] == 2

def test_metacalculation_invalid_csv():
    bad_csv = "not,a,valid,csv\n1,2,3"
    response = client.post(
        "/metacalculation",
        content=bad_csv,
        headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 400
    assert "detail" in response.json()