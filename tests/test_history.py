def test_history_empty(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_history_after_weather(client):
    from unittest.mock import AsyncMock, patch

    mock_response = AsyncMock()
    mock_response.text = "+20°C+50%"
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        client.get("/weather?city=Paris")

    response = client.get("/history?limit=5")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert history[0]["city"] == "Paris"

