"""Per-browser data isolation.

VeriDoc has no login system, so instead of a username/password, each browser
generates its own unguessable random ID (a UUIDv4, ~122 bits of randomness)
and sends it as the `X-User-Id` header on every request. The server treats
this exactly like a bearer token: every query that touches a Document (and,
through it, every child record - content, extractions, review items, chunks,
audit logs) is filtered by owner_id, and any request for a resource owned by
a different owner_id gets a plain 404, never a 403 (so we don't even confirm
that the resource exists for someone else).

This is intentionally NOT a full auth system (no password, no server-side
session, no protection if someone's ID leaks) - it is the smallest change
that stops the literal bug reported: two different browsers/users seeing each
other's data by default, which is what happens when there is no scoping at
all. If real accounts/login are added later, owner_id is exactly the column
a real `user.id` would replace - no other code needs to change.
"""
from fastapi import Header, HTTPException


def get_owner_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Missing X-User-Id header. The client must send a persistent per-browser identifier "
                   "on every request so data can be kept isolated between users.",
        )
    # Bound the length so a client can't smuggle an oversized/garbage value into the DB column.
    return x_user_id.strip()[:64]
