from .start import router as start_router
from .expenses import router as expenses_router
from .stats import router as stats_router
from .settings import router as settings_router
from .echo import router as echo_router
print("Loaded handlers package")

__all__ = [
    "start_router",
    "expenses_router",
    "stats_router",
    "echo_router",
]
