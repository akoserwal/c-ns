"""Error classes"""


class AppError(Exception):
    """All app errors defined on this"""

    pass


class ConflictError(AppError):
    """Storage and update errors"""

    pass


class DatabaseError(AppError):
    """Any database error"""

    pass
