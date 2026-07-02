from __future__ import annotations


class FOSTLedgerError(Exception):
    """Base exception for fost-agent-ledger."""


class SerializationError(FOSTLedgerError):
    """Raised when a JSON value cannot be decoded into the expected model."""


class StageFrozenError(FOSTLedgerError):
    """Raised when code attempts to modify a frozen ledger stage."""


class MissingRecordError(FOSTLedgerError):
    """Raised when a record identifier cannot be found."""


class ValidationError(FOSTLedgerError):
    """Raised for validator misuse that should be surfaced to callers."""


class UnknownModeError(FOSTLedgerError):
    """Raised when a mode has no finite public contract and fallback was not requested."""
