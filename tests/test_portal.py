import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from drone_fleet.api import FleetAPI, FastAPI
from drone_fleet.policy import engine


def test_portal_endpoints():
    if FastAPI is None:
        return
    api = FleetAPI(rate_limit=10)
    from fastapi.testclient import TestClient
    client = TestClient(api.app)
    token_resp = client.post('/token', data={'username':'admin','password':'admin'})
    t = token_resp.json()['access_token']
    headers = {'X-API-Key':'secret', 'Authorization': f'Bearer {t}'}
    resp = client.get('/portal/keys', headers=headers)
    assert resp.status_code == 200
    new_key = client.post('/portal/keys', headers=headers).json()['new_key']
    assert new_key
    del_resp = client.delete(f'/portal/keys/{new_key}', headers=headers)
    assert del_resp.status_code == 200


def test_policy_denies_login(tmp_path, monkeypatch):
    if FastAPI is None:
        return
    p = tmp_path/'p.yml'
    p.write_text('user:\n  login: deny\n')
    engine.path = p
    engine.load()
    api = FleetAPI()
    from fastapi.testclient import TestClient
    client = TestClient(api.app)
    resp = client.post('/token', data={'username':'operator','password':'operator'})
    assert resp.status_code == 403
    engine.path = 'policies.yaml'
    engine.load()
