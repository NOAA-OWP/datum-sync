class TransformError(BaseException):
    """Raised when a valid transformation between input and output CRS cannot be found"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ZConversionWarning(UserWarning):
    """Raised to alert user that z values may not have been convereted due to CRS selection.

    This may or may not be intentional
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
