from .start import router as start_router
from .expenses import router as expenses_router
from .echo import router as echo_router
print("Loaded handlers package")

__all__ = [
    "start_router",
    "expenses_router",
    "echo_router",
]
