from enum import Enum
from typing import Set

class Role(str, Enum):
    ADMIN = "Administrator"
    OPERATOR = "Operator"
    USER = "User"

ROLE_PERMISSIONS: dict[str, Set[str]] = {
    Role.ADMIN.value: {
        "server:read",
        "server:start",
        "server:stop",
        "server:restart",
        "server:logs",
        "server:rcon",
        "users:read",
        "users:write",
        "audit:read",
        "backup:read",
        "backup:create",
        "backup:restore",
        "metrics:read",
        "minecraft:link",
    },
    Role.OPERATOR.value: {
        "server:read",
        "server:start",
        "server:stop",
        "server:restart",
        "server:logs",
        "server:rcon",
        "backup:read",
        "backup:create",
        "metrics:read",
        "minecraft:link",
    },
    Role.USER.value: {
        "server:read",
        "metrics:read",
        "minecraft:link",
    }
}

def has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms
