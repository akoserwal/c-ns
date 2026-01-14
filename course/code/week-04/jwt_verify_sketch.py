from __future__ import annotations

"""
JWT verification sketch (typical shape).

This file is intentionally "infra-ish": it demonstrates how you would verify a JWT
issued by an IdP (e.g., Keycloak) using the realm JWKS endpoint.

You don't need a live Keycloak instance to read this. To run it, you'd need:
- a real ISSUER URL
- a real AUDIENCE (client id)
- a real token string to verify
"""

from dataclasses import dataclass

import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class Principal:
    sub: str
    roles: set[str]


def verify_access_token(*, token: str, issuer: str, audience: str) -> dict:
    jwks_url = f"{issuer}/protocol/openid-connect/certs"
    jwk_client = PyJWKClient(jwks_url)

    signing_key = jwk_client.get_signing_key_from_jwt(token).key
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
    )
    return payload


def principal_from_claims(claims: dict) -> Principal:
    # Keycloak commonly puts realm roles in: realm_access.roles
    realm_access = claims.get("realm_access") or {}
    roles = set(realm_access.get("roles") or [])
    return Principal(sub=str(claims.get("sub")), roles=roles)


def demo() -> None:
    issuer = "https://keycloak.example/realms/myrealm"
    audience = "my-api"
    token = "<paste token here>"

    # claims = verify_access_token(token=token, issuer=issuer, audience=audience)
    # p = principal_from_claims(claims)
    # print(p)

    print(
        "Edit issuer/audience/token and uncomment in demo() to verify a real token."
    )


if __name__ == "__main__":
    demo()

