"""Role-based authorization interface (Phase 6).

**No real authentication system exists yet** -- there is no login, no
token issuance, no user database. This module defines the INTERFACE a
real auth system would plug into (a FastAPI dependency returning a
`CurrentUser`, and a `require_role()` dependency factory that endpoints
declare against), and wires it onto the three endpoints that expose raw
submission content or bulk data (export, bulk comment import, annotation
import) as a concrete demonstration -- not applied blanket across every
endpoint, since retrofitting auth onto read endpoints that return no
sensitive raw text is lower priority than the three that do.

**Until a real identity provider is wired in, `get_current_user` returns
a default ADMIN user for every request** -- this is a development-mode
default, stated here explicitly rather than left to be discovered the
hard way. Before any real deployment handling genuine public submissions,
`get_current_user` MUST be replaced with a real authentication check
(e.g. verifying a session cookie or bearer token against a real user
store) -- see docs/backend/PRIVACY_AND_ACCESS_CONTROL.md for exactly
which controls are implemented versus which require that deployment step.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass

from fastapi import Depends, HTTPException


class Role(str, enum.Enum):
    PUBLIC = "public"
    RESEARCHER = "researcher"
    ADMIN = "admin"


_ROLE_RANK = {Role.PUBLIC: 0, Role.RESEARCHER: 1, Role.ADMIN: 2}


@dataclass
class CurrentUser:
    user_id: str
    role: Role


def get_current_user() -> CurrentUser:
    """Development-mode default: every request is treated as an admin.
    Replace this function's body with a real authentication check before
    any deployment that handles genuine public submissions."""
    return CurrentUser(user_id="dev-default-admin", role=Role.ADMIN)


def require_role(minimum_role: Role):
    def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if _ROLE_RANK[current_user.role] < _ROLE_RANK[minimum_role]:
            raise HTTPException(
                status_code=403,
                detail=f"Requires role '{minimum_role.value}' or higher; current role is '{current_user.role.value}'.",
            )
        return current_user

    return _dependency
