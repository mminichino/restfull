##
##

import attr
import json


@attr.s
class JsonObject:
    data_dict: dict = attr.ib()

    @property
    def as_dict(self) -> dict:
        return self.data_dict

    @property
    def as_string(self) -> str:
        return json.dumps(self.data_dict)

    @property
    def formatted(self) -> str:
        return json.dumps(self.data_dict, indent=2)


@attr.s
class JsonList:
    data_list: list = attr.ib()

    @property
    def as_list(self) -> list:
        return self.data_list

    @property
    def as_string(self) -> str:
        return json.dumps(self.data_list)

    @property
    def formatted(self) -> str:
        return json.dumps(self.data_list, indent=2)

    @property
    def size(self) -> int:
        return len(self.data_list)

    def sorted(self, key: str) -> list:
        return sorted(self.data_list, key=lambda d: d[key])
