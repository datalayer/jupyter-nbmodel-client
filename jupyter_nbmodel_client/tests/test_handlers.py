import json


async def test_get(jp_fetch):
    response = await jp_fetch("jupyter-nbmodel-client/ping")

    assert response.code == 200
    payload = json.loads(response.body)
    assert payload == {
        "ping_response": "pong"
    }
