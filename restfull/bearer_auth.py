##
##

from restfull.base_auth import RestAuthBase


class BearerAuth(RestAuthBase):

    def __init__(self, token: str):
        self.profile_token = token
        self.request_headers = {
            "Authorization": f"Bearer {self.profile_token}",
        }

    def __call__(self, r):
        r.headers.update(self.request_headers)
        return r

    def get_header(self):
        return self.request_headers
