##
##

from restfull.base_auth import RestAuthBase


class NoAuth(RestAuthBase):

    def __init__(self):
        self.request_headers = {}

    def __call__(self, r):
        return r

    def get_header(self):
        return self.request_headers
