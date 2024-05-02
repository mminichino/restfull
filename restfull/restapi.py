##
##

import os
import logging
import json
import requests
import warnings
import asyncio
import ssl
from restfull.base_auth import RestAuthBase
from restfull.data import JsonObject, JsonList
from typing import Union
from requests.adapters import HTTPAdapter, Retry
from aiohttp import ClientSession, TCPConnector
from pytoolbase.retry import retry
from pytoolbase.exceptions import NonFatalError
if os.name == 'nt':
    import certifi_win32
    certifi_where = certifi_win32.wincerts.where()
else:
    import certifi
    certifi_where = certifi.where()

warnings.filterwarnings("ignore")
logger = logging.getLogger('restfull.restapi')
logger.addHandler(logging.NullHandler())
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)


class RetryableError(NonFatalError):
    pass


class NonRetryableError(NonFatalError):
    pass


class RestAPI(object):

    def __init__(self,
                 auth_class: RestAuthBase,
                 hostname: str = '127.0.0.1',
                 use_ssl: bool = True,
                 verify: bool = True,
                 port: Union[int, None] = None):
        self.hostname = hostname
        self.auth_class = auth_class
        self.ssl = use_ssl
        self.verify = verify
        self.port = port
        self.scheme = 'https' if self.ssl else 'http'
        self.response_text = None
        self.response_dict: Union[list, dict] = {}
        self.response_code = 200
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.ssl_context = ssl.create_default_context()
        self.ssl_context.load_verify_locations(certifi_where)

        self.request_headers = self.auth_class.get_header()
        self.session = requests.Session()
        retries = Retry(total=10,
                        backoff_factor=0.01)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        if not port:
            if use_ssl:
                self.port = 443
            else:
                self.port = 80

        self.url_prefix = f"{self.scheme}://{self.hostname}:{self.port}"

    def get(self, endpoint: str):
        url = self.build_url(endpoint)
        self.reset()
        response = self.session.get(url, auth=self.auth_class, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def get_by_page(self, endpoint: str, page_tag: str = "page", page: int = 1, per_page_tag: Union[str, None] = None, per_page: int = 10):
        _endpoint = self.paged_endpoint(endpoint, page_tag, page, per_page_tag, per_page)
        url = self.build_url(_endpoint)
        self.reset()
        response = self.session.get(url, auth=self.auth_class, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def post(self, endpoint: str, body: dict):
        url = self.build_url(endpoint)
        self.reset()
        response = self.session.post(url, auth=self.auth_class, json=body, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def patch(self, endpoint: str, body: dict):
        url = self.build_url(endpoint)
        self.reset()
        response = self.session.patch(url, auth=self.auth_class, json=body, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def put(self, endpoint: str, body: dict):
        url = self.build_url(endpoint)
        self.reset()
        response = self.session.put(url, auth=self.auth_class, json=body, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def delete(self, endpoint: str):
        url = self.build_url(endpoint)
        self.reset()
        response = self.session.delete(url, auth=self.auth_class, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def validate(self):
        if 200 <= self.response_code < 400:
            return self
        elif 400 <= self.response_code < 500:
            raise RetryableError(f"code: {self.response_code} response: {self.response_text}")
        else:
            raise NonRetryableError(f"code: {self.response_code} response: {self.response_text}")

    def json(self, data_key: Union[str, None] = None):
        try:
            if data_key is None:
                return json.loads(self.response_text)
            else:
                return json.loads(self.response_text).get(data_key)
        except (json.decoder.JSONDecodeError, AttributeError):
            return {}

    def as_json(self, data_key: Union[str, None] = None):
        try:
            if data_key is None:
                self.response_dict = json.loads(self.response_text)
            else:
                self.response_dict = json.loads(self.response_text).get(data_key)
        except (json.decoder.JSONDecodeError, AttributeError):
            self.response_dict = {}
        return self

    def filter(self, key: str, value: str):
        if type(self.response_dict) is list:
            self.response_dict = [item for item in self.response_dict if item.get(key) == value]
        else:
            self.response_dict = self.response_dict if dict(self.response_dict).get(key) == value else {}
        return self

    def list_item(self, index: int):
        try:
            return list(self.records())[index]
        except IndexError:
            return None

    def list(self):
        return list(self.records())

    def json_key(self, key: str):
        record = self.record()
        return record.get(key)

    def records(self):
        if type(self.response_dict) is list:
            for element in self.response_dict:
                yield element
        else:
            yield self.response_dict

    def record(self):
        return next(self.records())

    def unique(self):
        if type(self.response_dict) is list and len(self.response_dict) > 1:
            raise ValueError("More than one object matches search criteria")
        return self.record()

    def page_count(self, total_tag: str = "total", pages_tag: str = "total_pages"):
        record = self.record()
        return record.get(total_tag), record.get(pages_tag)

    def json_object(self) -> JsonObject:
        return JsonObject(self.response_dict)

    def json_list(self) -> JsonList:
        return JsonList(self.response_dict)

    @property
    def is_present(self) -> bool:
        if self.response_dict:
            return True
        else:
            return False

    @property
    def is_empty(self) -> bool:
        if self.response_dict:
            return False
        else:
            return True

    @property
    def code(self):
        return self.response_code

    def reset(self):
        self.response_dict = {}

    @staticmethod
    def paged_endpoint(endpoint: str, page_tag: str = "page", page: int = 1, per_page_tag: Union[str, None] = None, per_page: int = 10) -> str:
        _endpoint = f"{endpoint}?{page_tag}={page}"
        if per_page_tag:
            _endpoint += f"&{per_page_tag}={per_page}"
        return _endpoint

    def build_url(self, endpoint: str) -> str:
        return f"{self.url_prefix}{endpoint}"

    @retry()
    async def get_data_async(self, endpoint: str, data_key: Union[str, None] = None):
        url = self.build_url(endpoint)
        conn = TCPConnector(ssl_context=self.ssl_context)
        async with ClientSession(headers=self.request_headers, connector=conn) as session:
            async with session.get(url, verify_ssl=self.verify) as response:
                response = await response.json()
                if data_key:
                    return response.get(data_key)
                else:
                    return response

    @retry()
    async def get_kv_async(self, endpoint: str, key: str, value: Union[str, int, bool], data_key: Union[str, None] = None):
        url = self.build_url(endpoint)
        conn = TCPConnector(ssl_context=self.ssl_context)
        async with ClientSession(headers=self.request_headers, connector=conn) as session:
            async with session.get(url, verify_ssl=self.verify) as response:
                response = await response.json()
                data = response.get(data_key) if data_key else response
                return [item for item in data if item.get(key) == value]
