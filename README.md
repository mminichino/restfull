# restfull 1.0.13

## Installing
```
$ pip install restfull
```

# Usage Examples

Basic API GET:
```
auth = BasicAuth("username", "password")
rest = RestAPI(auth, "example.com")
endpoint = "/api/users/1"
data = rest.get(endpoint).validate().as_json().record()
assert data.get("data", {}).get("id") == 1
```

Get record with paged API (specifically getting page 2)
```
auth = BasicAuth("username", "password")
rest = RestAPI(auth, "example.com")
endpoint = "/api/users"
data = rest.get_by_page(endpoint, page=2).validate().as_json("data").list_item(2)
assert data.get("id") == 9
```

Get all records from paged API (assumes records are in an array assigned to the "data" key):
```
auth = BasicAuth("username", "password")
rest = RestAPI(auth, "example.com")
endpoint = "/api/users"
data = rest.get_paged(endpoint).validate().json_list()
assert data.size == 12
```
