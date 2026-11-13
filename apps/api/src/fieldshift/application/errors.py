"""Application errors; mapped to HTTP by fieldshift.main."""


class NotFound(LookupError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


class InvalidInput(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message
