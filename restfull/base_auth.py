##
##

from requests.auth import AuthBase


class RestAuthBase(AuthBase):
    request_headers = {}

    def __call__(self, r):
        raise NotImplementedError("Auth hooks must be callable.")

    def get_header(self):
        return self.request_headers
