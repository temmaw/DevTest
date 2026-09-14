from unittest.mock import AsyncMock, patch


def test_weather_success(client):
    mock_response = AsyncMock()
    mock_response.text = "+15°C+60%"
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        response = client.get("/weather?city=London")

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
    assert "15" in data["temperature"]
    assert "60" in data["humidity"]
    assert data["saved"] is True

def test_weather_api_error(client):
    with patch("httpx.AsyncClient.get", side_effect=Exception("timeout")):
        response = client.get("/weather?city=London")

    assert response.status_code == 503
    assert "API error" in response.json()["detail"]

def test_weather_missing_city(client):
    response = client.get("/weather")
    assert response.status_code == 422  # FastAPI validation error
