# -*- coding: utf-8 -*-

def test_index(test_client):
    response = test_client.get("/")
    assert response.status_code == 200


def test_config_no_token(test_client):
    response = test_client.get("/config/")
    assert response.status_code == 404


def test_update_from_name(test_client):
    response = test_client.post("/update/from_name/", data={"name": "test_filename_with_ümlaut"})
    print(response.json)
    assert response.status_code == 200
    assert response.json["success"]
