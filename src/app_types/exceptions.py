

class AgencyNotFound(Exception):
    def __init__(self, detail: str | None = None) -> None:
        if not detail:
            detail = "Agency with provided id was not found"
        self.detail = detail

    def __str__(self) -> str:
        return f"Agency not found: {self.detail}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(detail={self.detail})"




