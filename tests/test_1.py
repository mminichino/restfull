#!/usr/bin/env python3

import logging
import pytest
import warnings
import asyncio
import unittest
from restfull.restapi import RestAPI, RetryableError, NotFoundError, NonRetryableError
from restfull.basic_auth import BasicAuth

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_1')
logger.addHandler(logging.NullHandler())


@pytest.mark.rest_api
@pytest.mark.asyncio
class TestMain(unittest.TestCase):

    @classmethod
    def setUp(cls):
        pass

    @classmethod
    def tearDown(cls):
        pass

    def test_1(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/1"
        data = rest.get(endpoint).validate().as_json().record()
        assert data.get("data", {}).get("id") == 1

    def test_2(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        data = rest.get_by_page(endpoint, page=2).validate().as_json("data").list_item(2)
        assert data.get("id") == 9

    def test_3(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        total, pages, data = rest.get_by_page(endpoint).validate().as_json().page_count()
        assert total == 12
        assert pages == 2

    def test_4(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/23"
        try:
            rest.get(endpoint).validate().as_json().record()
        except NotFoundError:
            return
        except (RetryableError, NonRetryableError):
            assert False
        assert False

    def test_5(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        body = {
            "name": "morpheus",
            "job": "leader"
        }
        data = rest.post(endpoint, body).validate().json()
        assert data.get("name") == "morpheus"

    def test_6(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/2"
        body = {
            "name": "morpheus",
            "job": "leader"
        }
        data = rest.put(endpoint, body).validate().json()
        assert data.get("name") == "morpheus"

    def test_7(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/2"
        body = {
            "name": "morpheus",
            "job": "leader"
        }
        data = rest.patch(endpoint, body).validate().json()
        assert data.get("name") == "morpheus"

    def test_8(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/2"
        code = rest.delete(endpoint).validate().code
        assert code == 204

    def test_9(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/1"
        data = rest.get(endpoint).validate().as_json("data").json_object()
        assert data.as_dict.get("id") == 1

    def test_10(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        data = rest.get_by_page(endpoint, page=2).validate().as_json("data").json_list()
        assert data.size == 6
        assert data.as_list[2].get("id") == 9

    def test_11(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        data = rest.get_paged(endpoint).validate().json_list()
        assert data.size == 12

    def test_12(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users/23"
        try:
            rest.get_paged(endpoint).validate().json_list()
        except NotFoundError:
            return
        except (RetryableError, NonRetryableError):
            assert False
        assert False

    async def test_13(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        total, pages, data = rest.get_by_page(endpoint).validate().as_json().page_count()

        if pages > 1:
            for result in asyncio.as_completed([rest.get_data_async(rest.paged_endpoint(endpoint, page=page), data_key="data") for page in range(2, pages + 1)]):
                block = await result
                data.extend(block)

        assert len(data) == total
        data_sorted = sorted(data, key=lambda d: d['id'])
        assert data_sorted[7].get("first_name") == "Lindsay"

    async def test_14(self):
        data = []
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/users"
        total, pages, _ = rest.get_by_page(endpoint).validate().as_json().page_count()

        for result in asyncio.as_completed([rest.get_kv_async(rest.paged_endpoint(endpoint, page=page), key="id", value=9, data_key="data") for page in range(1, pages + 1)]):
            block = await result
            data.extend(block)

        assert len(data) == 1
        assert data[0].get("first_name") == "Tobias"

    async def test_15(self):
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/unknown/23"

        try:
            total, pages, _ = rest.get_by_page(endpoint).validate().as_json().page_count()
        except NotFoundError:
            return
        except Exception as e:
            logging.exception(e)
            assert False

        assert False

    async def test_16(self):
        data = []
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/unknown/23"
        pages = 2

        try:
            for result in asyncio.as_completed([rest.get_data_async(rest.paged_endpoint(endpoint, page=page), data_key="data") for page in range(2, pages + 1)]):
                try:
                    block = await result
                    data.extend(block)
                except Exception:
                    raise
        except NotFoundError:
            return

        assert False

    async def test_17(self):
        data = []
        auth = BasicAuth("username", "password")
        rest = RestAPI(auth, "reqres.in")
        endpoint = "/api/unknown/23"
        pages = 2

        try:
            for result in asyncio.as_completed([rest.get_kv_async(rest.paged_endpoint(endpoint, page=page), key="id", value=9, data_key="data") for page in range(1, pages + 1)]):
                try:
                    block = await result
                    data.extend(block)
                except Exception:
                    raise
        except NotFoundError:
            return

        assert False
