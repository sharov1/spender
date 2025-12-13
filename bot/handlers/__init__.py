from .start import router as start_router
from .expenses import router as expenses_router
from .stats import router as stats_router
from .settings import router as settings_router
from .main_menu_handlers import router as main_menu_router
from .history import router as history_router
from .echo import router as echo_router
print("Loaded handlers package")

__all__ = [
    "start_router",
    "expenses_router",
    "stats_router",
    "settings_router",
    "main_menu_router",
    "history_router",
    "echo_router",
    
]
