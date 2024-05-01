##
##

import base64
from restfull.base_auth import RestAuthBase


class BasicAuth(RestAuthBase):

    def __init__(self, username, password):
        self.username = username
        self.password = password
        auth_hash = f"{self.username}:{self.password}"
        auth_bytes = auth_hash.encode('ascii')
        auth_encoded = base64.b64encode(auth_bytes)

        self.request_headers = {
            "Authorization": f"Basic {auth_encoded.decode('ascii')}",
        }

    def __call__(self, r):
        r.headers.update(self.request_headers)
        return r

    def get_header(self):
        return self.request_headers
