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


class PermissionDeniedError(NonFatalError):
    pass


class NotFoundError(NonFatalError):
    pass


class RateLimitError(NonFatalError):
    pass


class InternalServerError(NonFatalError):
    pass


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
        self.success_start = 200
        self.success_end = 299
        self.permission_denied_code = 403
        self.not_found_code = 404
        self.rate_limit_code = 429
        self.server_error_code = 500
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

    def set_success_range(self, start: int, end: int):
        self.success_start = start
        self.success_end = end

    def set_permission_denied_code(self, code: int):
        self.permission_denied_code = code

    def set_not_found_code(self, code: int):
        self.not_found_code = code

    def set_rate_limit_code(self, code: int):
        self.rate_limit_code = code

    def set_server_error_code(self, code: int):
        self.server_error_code = code

    def get(self, endpoint: str):
        url = self.build_url(endpoint)
        self.reset()
        logger.debug(f"GET {url}")
        response = self.session.get(url, auth=self.auth_class, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def get_by_page(self, endpoint: str, page_tag: str = "page", page: int = 1, per_page_tag: Union[str, None] = None, per_page: int = 10):
        _endpoint = self.paged_endpoint(endpoint, page_tag, page, per_page_tag, per_page)
        url = self.build_url(_endpoint)
        self.reset()
        logger.debug(f"GET {url}")
        response = self.session.get(url, auth=self.auth_class, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def post(self, endpoint: str, body: dict):
        url = self.build_url(endpoint)
        self.reset()
        logger.debug(f"POST {url}")
        response = self.session.post(url, auth=self.auth_class, json=body, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def patch(self, endpoint: str, body: dict):
        url = self.build_url(endpoint)
        self.reset()
        logger.debug(f"PATCH {url}")
        response = self.session.patch(url, auth=self.auth_class, json=body, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def put(self, endpoint: str, body: dict):
        url = self.build_url(endpoint)
        self.reset()
        logger.debug(f"PUT {url}")
        response = self.session.put(url, auth=self.auth_class, json=body, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def delete(self, endpoint: str):
        url = self.build_url(endpoint)
        self.reset()
        logger.debug(f"DELETE {url}")
        response = self.session.delete(url, auth=self.auth_class, verify=self.verify)
        self.response_text = response.text
        self.response_code = response.status_code
        return self

    def validate(self):
        logger.debug(f"Validating return code {self.response_code}: {self.response_text}")
        if self.success_start <= self.response_code < self.success_end:
            return self
        elif self.response_code == self.permission_denied_code:
            raise PermissionDeniedError(self.response_text)
        elif self.response_code == self.not_found_code:
            raise NotFoundError(self.response_text)
        elif self.response_code == self.rate_limit_code:
            raise RateLimitError(self.response_text)
        elif self.response_code == self.server_error_code:
            raise InternalServerError(self.response_text)
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

    def page_count(self, total_tag: str = "total", pages_tag: str = "total_pages", data_key="data", cursor: str = None, category: str = None):
        record = self.record()
        data = record.get(data_key)
        if cursor is not None:
            record = record.get(cursor, {})
        if category is not None:
            record = record.get(category, {})
        return record.get(total_tag), record.get(pages_tag), data

    def json_object(self) -> JsonObject:
        return JsonObject(self.response_dict)

    def json_list(self) -> JsonList:
        return JsonList(self.response_dict)

    async def get_paged_endpoint(self,
                                 endpoint: str,
                                 page_tag: str = "page",
                                 total_tag: str = "total",
                                 pages_tag: str = "total_pages",
                                 per_page_tag: str = None,
                                 per_page: int = 10,
                                 data_key="data",
                                 cursor: str = None,
                                 category: str = None):
        total, pages, data = self.get_by_page(endpoint, page_tag, 1, per_page_tag, per_page).validate().as_json().page_count(total_tag, pages_tag, data_key, cursor, category)

        if pages > 1:
            for result in asyncio.as_completed([self.get_data_async(self.paged_endpoint(endpoint, page_tag, page, per_page_tag, per_page),
                                                                    data_key=data_key) for page in range(2, pages + 1)]):
                block = await result
                data.extend(block)

        return data

    def get_paged(self,
                  endpoint: str,
                  page_tag: str = "page",
                  total_tag: str = "total",
                  pages_tag: str = "total_pages",
                  per_page_tag: str = None,
                  per_page: int = 10,
                  data_key="data",
                  cursor: str = None,
                  category: str = None):
        self.response_dict = self.loop.run_until_complete(self.get_paged_endpoint(endpoint, page_tag, total_tag, pages_tag, per_page_tag, per_page, data_key, cursor, category))
        return self

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
                if self.response_code < 400:
                    self.response_code = response.status
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
