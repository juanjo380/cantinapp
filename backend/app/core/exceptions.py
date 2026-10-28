"""Excepciones de aplicación. El status_code define el HTTP que devuelve la API
(RNF-06): 401, 403, 404, 409, 422 y 500 por defecto."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message: str = "Error interno del servidor") -> None:
        super().__init__(message)
        self.message = message


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class UnprocessableError(AppError):
    status_code = 422


class TooManyRequestsError(AppError):
    status_code = 429
