Release type: major

feat!: [#53756] Add support for arbitrary token endpoint

BREAKING CHANGE:

This replaces the `auth_server` and `auth_realm` arguments to the authenticated
clients with a single `token_endpoint`. Users can maintain support for Keycloak
by utilising the new `keycloak_token_endpoint` function:
```
AuthenticatedAsyncHTTPXClient(
    client_id="AzureDiamond",
    client_secret="hunter2",
    token_endpoint=keycloak_token_endpoint(
        auth_server=parse_obj_as(AnyHttpUrl, "https://keycloak.example.org/auth"),
        auth_realm="mordor",
    ),
)
```
