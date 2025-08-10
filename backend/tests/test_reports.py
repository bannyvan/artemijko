from app.security import create_access_token

def auth_headers(user_id: int):
    token = create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


def test_reports_summary(client):
    headers = auth_headers(1)
    r = client.get("/reports/summary", params={"period": "day"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["period"] == "day"
    assert "items" in data