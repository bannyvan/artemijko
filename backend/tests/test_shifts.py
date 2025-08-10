from .test_auth import make_init_data


def auth_headers_from_client(client):
    r = client.post("/auth/telegram", params={"initData": make_init_data(40001)})
    access = r.json()["access_token"]
    return {"Authorization": f"Bearer {access}"}


def test_shift_lifecycle(client):
    headers = auth_headers_from_client(client)

    r = client.post("/shifts/start", headers={**headers, "Idempotency-Key": "idem-1"}, json={})
    assert r.status_code == 200

    r = client.post("/breaks/start", headers=headers, json={"type": "lunch"})
    assert r.status_code == 200

    r = client.post("/breaks/finish", headers=headers)
    assert r.status_code == 200

    r = client.post("/shifts/pause", headers=headers)
    assert r.status_code == 200

    r = client.post("/shifts/resume", headers=headers)
    assert r.status_code == 200

    r = client.post("/shifts/finish", headers={**headers, "Idempotency-Key": "idem-2"})
    assert r.status_code == 200