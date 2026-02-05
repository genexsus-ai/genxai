"""Global test configuration."""

import warnings


warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r"unclosed database in <sqlite3\.Connection",
)
