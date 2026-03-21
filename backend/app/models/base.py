"""Base model utilities — portable types that work on both PostgreSQL and SQLite."""

import uuid

from sqlalchemy import String, Text, types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class PortableUUID(types.TypeDecorator):
    """UUID type that works on PostgreSQL (native UUID) and SQLite (String(36)).

    This allows tests to run on SQLite locally while production uses PostgreSQL.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class PortableJSON(types.TypeDecorator):
    """JSON type that works on PostgreSQL (JSONB) and SQLite (Text as JSON)."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB)
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql":
            import json
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            import json
            return json.loads(value)
        return value
