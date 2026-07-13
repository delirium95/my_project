class AuthenticationError(ValueError):
    """Base error for a rejected authentication request."""


class EmailAlreadyRegisteredError(AuthenticationError):
    """Raised when a registration email is already in use."""


class InvalidCredentialsError(AuthenticationError):
    """Raised for an invalid email-password pair without leaking which part failed."""


class InvalidTokenError(AuthenticationError):
    """Raised when a bearer token is malformed, expired, or cannot be verified."""


class RefreshTokenStoreUnavailableError(AuthenticationError):
    """Raised when refresh-token replay protection cannot be safely checked."""
