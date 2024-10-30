#!/usr/bin/env python3

import os
import logging
import pytest
import warnings
import unittest
import hashlib
import tempfile
from restfull.restapi import RestAPI, RetryableError, InternalServerError, NonRetryableError
from restfull.no_auth import NoAuth

warnings.filterwarnings("ignore")
logger = logging.getLogger('tests.test_2')
logger.addHandler(logging.NullHandler())


@pytest.mark.rest_api
@pytest.mark.http_test
@pytest.mark.asyncio
class TestMain(unittest.TestCase):

    @classmethod
    def setUp(cls):
        pass

    @classmethod
    def tearDown(cls):
        pass

    def test_1(self):
        rest = RestAPI(NoAuth(), "google.com", True, True)
        endpoint = "/generate_204"
        code, data = rest.get(endpoint).response()
        assert code == 204

    def test_2(self):
        rest = RestAPI(NoAuth(), "captive.apple.com", True, True)
        endpoint = "/"
        code, data = rest.get(endpoint).response()
        assert code == 200

    def test_3(self):
        rest = RestAPI(NoAuth(), "detectportal.firefox.com", True, True)
        endpoint = "/success.txt"
        code, data = rest.get(endpoint).response()
        assert code == 200
        assert data.strip() == "success"

    def test_4(self):
        rest = RestAPI(NoAuth(), "google.com", False)
        endpoint = "/generate_204"
        code, data = rest.get(endpoint).response()
        assert code == 204

    def test_5(self):
        rest = RestAPI(NoAuth(), "captive.apple.com", False)
        endpoint = "/"
        code, data = rest.get(endpoint).response()
        assert code == 200

    def test_6(self):
        rest = RestAPI(NoAuth(), "detectportal.firefox.com", False)
        endpoint = "/success.txt"
        code, data = rest.get(endpoint).response()
        assert code == 200
        assert data.strip() == "success"

    def test_7(self):
        rest = RestAPI(NoAuth(), "httpstat.us", False)
        rest.retry_server_errors()
        endpoint = "/500"
        try:
            rest.get(endpoint).validate().response()
        except RetryableError:
            return
        assert False

    def test_8(self):
        rest = RestAPI(NoAuth(), "httpstat.us", False)
        endpoint = "/500"
        try:
            rest.get(endpoint).validate().response()
        except InternalServerError:
            return
        assert False

    def test_9(self):
        rest = RestAPI(NoAuth(), "httpstat.us", False)
        rest.retry_server_errors()
        endpoint = "/504"
        try:
            rest.get(endpoint).validate().response()
        except RetryableError:
            return
        assert False

    def test_10(self):
        rest = RestAPI(NoAuth(), "httpstat.us", False)
        endpoint = "/504"
        try:
            rest.get(endpoint).validate().response()
        except NonRetryableError:
            return
        assert False

    def test_11(self):
        rest = RestAPI(NoAuth(), "link.testfile.org", True, True)
        endpoint = "/PDF10MB"
        data = rest.get_bytes(endpoint).validate().content()
        hasher = hashlib.sha1()
        hasher.update(data)
        assert hasher.hexdigest() == "f95fa54f809dc33234ed81c2c4326c44633b21a3"

    def test_12(self):
        rest = RestAPI(NoAuth(), "link.testfile.org", True, True)
        endpoint = "/PDF200MB"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, 'file.pdf')
            logger.debug(f"Temp file: {temp_file}")
            rest.download(endpoint, temp_file)
            hasher = hashlib.sha1()
            with open(temp_file, 'rb') as file:
                while True:
                    chunk = file.read(1048576)
                    if not chunk:
                        break
                    hasher.update(chunk)
            assert hasher.hexdigest() == "a4b96d4a052aaa64f0e8c4ccc0549e76a42c0abf"
