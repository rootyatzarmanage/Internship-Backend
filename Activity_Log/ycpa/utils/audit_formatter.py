from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


SENSITIVE_FIELDS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "authorization",
}


def normalize_value(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            str(k): normalize_value(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [normalize_value(v) for v in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def display_value(value: Any) -> str:
    value = normalize_value(value)

    if value is None:
        return "None"

    if isinstance(value, bool):
        return str(value).lower()

    return str(value)


def generate_audit_changes(
    old_data: dict,
    new_data: dict,
):
    changes = {}
    messages = []

    for field, new_value in new_data.items():

        if field.lower() in SENSITIVE_FIELDS:
            continue

        old_value = old_data.get(field)

        old_normalized = normalize_value(old_value)
        new_normalized = normalize_value(new_value)

        if old_normalized == new_normalized:
            continue

        changes[field] = {
            "old": old_normalized,
            "new": new_normalized,
        }

        messages.append(
            f"Changed {field.replace('_', ' ')} "
            f"from {display_value(old_value)} "
            f"to {display_value(new_value)}"
        )

    return changes, messages


def generate_activity_description(
    action: str,
    entity_type: str,
    changes: dict | None = None,
    messages: list[str] | None = None,
) -> str:
    """
    Generate descriptions for CREATE, UPDATE and DELETE operations.
    """

    action = action.upper()
    entity = entity_type.replace("_", " ").lower()

    if action in {"CREATED", "CREATE"}:
        return f"Created {entity}"

    if action in {"DELETED", "DELETE"}:
        return f"Deleted {entity}"

    if messages:
        return "; ".join(messages)

    if changes:
        descriptions = []

        for field, values in changes.items():
            descriptions.append(
                f"Changed {field.replace('_', ' ')} "
                f"from {display_value(values.get('old'))} "
                f"to {display_value(values.get('new'))}"
            )

        return "; ".join(descriptions)

    return f"Updated {entity}"