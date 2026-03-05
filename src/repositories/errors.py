from dataclasses import dataclass


@dataclass
class RepositoryError(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def require_non_empty(value: str, *, field_name: str) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise RepositoryError("VALIDATION_ERROR", f"{field_name} is required")
