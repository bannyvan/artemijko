from .test_auth import make_init_data


def auth_headers_from_client(client):
    r = client.post("/auth/telegram", params={"initData": make_init_data(50001)})
    access = r.json()["access_token"]
    return {"Authorization": f"Bearer {access}"}


def test_requests_flow(client):
    headers = auth_headers_from_client(client)

    r = client.get("/requests", headers=headers)
    assert r.status_code == 200

    r = client.post("/requests", headers=headers, json={
        "type": "dayoff",
        "from_date": "2025-01-01",
        "to_date": "2025-01-01",
        "days": 1,
        "comment": "test"
    })
    assert r.status_code == 200
    req_id = r.json()["id"]

    # Patch requires manager/admin; we skip here