"""
Menu Registry & Routing Dispatcher for TruthGPT Interface Subsystem.
====================================================================
Provides dynamic registration, lifecycle dispatching, and lookup for all
interactive menu hubs across the TruthGPT ecosystem.
"""
from __future__ import annotations

import inspect
import logging
import sys
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union

from interface.exceptions import DuplicateMenuError, MenuNotFoundError, ThemeNotFoundError
from interface.interfaces import BaseMenu, BaseThemeEngine, BaseTUIComponent
from interface.types import MenuCategory, MenuItem, ThemePalette, ThemeType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Menu Option Data Container
# ---------------------------------------------------------------------------

class MenuOption:
    """Descriptor for a registered menu option and route."""

    def __init__(
        self,
        id: str = "",
        title: str = "",
        key: Optional[str] = None,
        name: Optional[str] = None,
        handler: Optional[Callable[..., Any]] = None,
        category: str = "General",
        description: str = "",
        shortcut: Optional[str] = None,
        icon: str = "📌",
        badge: Optional[str] = None,
        is_async: bool = True,
        **kwargs: Any,
    ) -> None:
        raw_key = key or id or name or ""
        self.id = (id or raw_key).lower().strip()
        self.key = raw_key.lower().strip()
        self.title = title or name or (self.key.replace("_", " ").title() if self.key else "")
        self.name = self.title
        self.handler = handler
        self.category = category
        self.description = description
        self.shortcut = shortcut
        self.icon = icon
        self.badge = badge
        self.is_async = is_async
        self.metadata = kwargs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "title": self.title,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "shortcut": self.shortcut,
            "icon": self.icon,
            "badge": self.badge,
        }

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            other_clean = other.lower().strip()
            return self.key == other_clean or self.id == other_clean or self.title.lower() == other_clean
        if isinstance(other, MenuOption):
            return self.key == other.key
        return super().__eq__(other)

    def __repr__(self) -> str:
        return f"<MenuOption id={self.id!r} title={self.title!r} category={self.category!r}>"


# ---------------------------------------------------------------------------
# Menu Registry
# ---------------------------------------------------------------------------

class MenuRegistry:
    """Centralized thread-safe registry for interface menu handlers and routes."""

    _lock = threading.RLock()
    _registry: Dict[str, Callable[..., Any]] = {}
    _metadata: Dict[str, MenuOption] = {}
    _classes: Dict[str, Type[Any]] = {}
    _initialized_defaults: bool = False

    @classmethod
    def register(
        cls,
        name: Optional[Union[str, Callable[..., Any]]] = None,
        handler: Optional[Callable[..., Any]] = None,
        title: str = "",
        category: Union[MenuCategory, str] = "General",
        description: str = "",
        shortcut: Optional[str] = None,
        icon: str = "📌",
        badge: Optional[str] = None,
        is_async: bool = True,
        overwrite: bool = True,
        key: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Register a menu handler. Can be used as a decorator or direct method call."""
        resolved_name = key or name

        def _do_register(target_fn_or_cls: Any, menu_name: str) -> Any:
            norm_key = menu_name.strip().lower()
            cat = category.value if isinstance(category, MenuCategory) else str(category)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ("key", "id", "name")}
            with cls._lock:
                if inspect.isclass(target_fn_or_cls):
                    cls._classes[norm_key] = target_fn_or_cls
                cls._registry[norm_key] = target_fn_or_cls
                cls._metadata[norm_key] = MenuOption(
                    id=norm_key,
                    key=norm_key,
                    title=title or menu_name.replace("_", " ").title(),
                    name=title or menu_name.replace("_", " ").title(),
                    handler=target_fn_or_cls,
                    category=cat,
                    description=description or getattr(target_fn_or_cls, "__doc__", "") or "",
                    shortcut=shortcut,
                    icon=icon,
                    badge=badge,
                    is_async=is_async,
                    **filtered_kwargs,
                )
            logger.debug(f"Registered menu: {norm_key} -> {target_fn_or_cls}")
            return target_fn_or_cls

        if callable(resolved_name) and handler is None:
            fn = resolved_name
            key_name = fn.__name__.replace("_menu", "").replace("handle_", "")
            return _do_register(fn, key_name)

        if isinstance(resolved_name, str) and handler is not None:
            return _do_register(handler, resolved_name)

        def decorator(fn_or_cls: Any) -> Any:
            key_name = str(resolved_name) if resolved_name else fn_or_cls.__name__.replace("_menu", "").replace("handle_", "")
            return _do_register(fn_or_cls, key_name)

        return decorator

    @classmethod
    def register_class(
        cls,
        name: str,
        menu_cls: Type[BaseMenu],
        overwrite: bool = True,
    ) -> None:
        """Register a BaseMenu class."""
        with cls._lock:
            key = name.strip().lower()
            cls._classes[key] = menu_cls
            cls.register(
                name=key,
                handler=menu_cls,
                title=getattr(menu_cls, "title", key.title()),
                category=getattr(menu_cls, "category", "General"),
                description=getattr(menu_cls, "description", ""),
                shortcut=getattr(menu_cls, "shortcut", None),
                icon=getattr(menu_cls, "icon", "📌"),
                overwrite=overwrite,
            )

    @classmethod
    def get(cls, key: str) -> Callable[..., Any]:
        """Retrieve registered handler by key."""
        cls._ensure_defaults()
        norm_key = key.strip().lower()
        with cls._lock:
            if norm_key not in cls._registry:
                raise MenuNotFoundError(
                    f"Menu route '{key}' is not registered.",
                    details={"available_menus": list(cls._registry.keys())},
                )
            return cls._registry[norm_key]

    @classmethod
    def get_menu(cls, key: str) -> MenuOption:
        """Retrieve registered MenuOption descriptor."""
        cls._ensure_defaults()
        norm_key = key.strip().lower()
        with cls._lock:
            if norm_key not in cls._metadata:
                raise MenuNotFoundError(f"Menu '{key}' not found in registry.")
            return cls._metadata[norm_key]

    @classmethod
    def get_handler(cls, key: str) -> Optional[Callable[..., Any]]:
        cls._ensure_defaults()
        norm_key = key.strip().lower()
        with cls._lock:
            return cls._registry.get(norm_key)

    @classmethod
    async def dispatch(cls, key: str, *args: Any, **kwargs: Any) -> Any:
        handler = cls.get(key)
        if inspect.iscoroutinefunction(handler):
            return await handler(*args, **kwargs)
        result = handler(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    @classmethod
    def list_menus(cls, category: Optional[Union[MenuCategory, str]] = None) -> List[MenuOption]:
        cls._ensure_defaults()
        with cls._lock:
            if category:
                target_cat = category.value if isinstance(category, MenuCategory) else str(category).lower()
                return [m for m in cls._metadata.values() if m.category.lower() == target_cat]
            return list(cls._metadata.values())

    @classmethod
    def create_menu_instance(cls, name: str, **kwargs: Any) -> Optional[BaseMenu]:
        cls._ensure_defaults()
        norm_key = name.strip().lower()
        with cls._lock:
            if norm_key in cls._classes:
                return cls._classes[norm_key](**kwargs)
            return None

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._registry.clear()
            cls._metadata.clear()
            cls._classes.clear()
            cls._initialized_defaults = False

    @classmethod
    def _ensure_defaults(cls) -> None:
        if cls._initialized_defaults:
            return
        with cls._lock:
            if cls._initialized_defaults:
                return
            cls._initialized_defaults = True
            cls._register_system_defaults()

    @classmethod
    def _register_system_defaults(cls) -> None:
        """Register the standard built-in TruthGPT menus."""
        # 1. Swarm
        try:
            from interface.swarm_menu import swarm_menu
            cls.register(
                name="swarm",
                handler=swarm_menu,
                title="Neural Reasoning Swarm",
                category=MenuCategory.SWARM.value,
                description="Swarm consensus, autonomous code generation, expert matrix",
                shortcut="1",
                icon="🧠",
            )
        except Exception:
            pass

        # 2. Blockchain
        try:
            from interface.blockchain_menu import blockchain_menu
            cls.register(
                name="blockchain",
                handler=blockchain_menu,
                title="Blockchain & Web3 Hub",
                category=MenuCategory.BLOCKCHAIN.value,
                description="Web3 wallets, smart contract audits, decentralized AI",
                shortcut="2",
                icon="⛓️",
            )
        except Exception:
            pass

        # 3. Communications
        try:
            from interface.comm_menu import comm_menu
            cls.register(
                name="comm",
                handler=comm_menu,
                title="Communications Hub",
                category=MenuCategory.COMMUNICATION.value,
                description="Discord, Telegram, Slack, WhatsApp bridge integrations",
                shortcut="3",
                icon="📡",
            )
        except Exception:
            pass

        # 4. Infrastructure
        try:
            from interface.infra_menu import infra_menu
            cls.register(
                name="infra",
                handler=infra_menu,
                title="Infrastructure & Cluster Ops",
                category=MenuCategory.INFRASTRUCTURE.value,
                description="Kubernetes clusters, distributed node topology, system health",
                shortcut="4",
                icon="🏗️",
            )
        except Exception:
            pass

        # 5. Model
        try:
            from interface.model_menu import model_menu
            cls.register(
                name="model",
                handler=model_menu,
                title="Model & Engine Configuration",
                category=MenuCategory.MODEL.value,
                description="DeepSeek, OpenAI, Claude, Gemini model routing and temperature",
                shortcut="5",
                icon="⚙️",
            )
        except Exception:
            pass

        # 6. Overdrive
        try:
            from interface.overdrive_menu import overdrive_menu
            cls.register(
                name="overdrive",
                handler=overdrive_menu,
                title="Overdrive Acceleration Kernels",
                category=MenuCategory.OVERDRIVE.value,
                description="Triton GPU kernels, speculative decoding, flash attention",
                shortcut="6",
                icon="⚡",
            )
        except Exception:
            pass

        # 7. Research
        try:
            from interface.research_menu import research_menu
            cls.register(
                name="research",
                handler=research_menu,
                title="Research Paper Library",
                category=MenuCategory.RESEARCH.value,
                description="Indexed research papers, theoretical proofs, kernel implementations",
                shortcut="7",
                icon="📚",
            )
        except Exception:
            pass

        # 8. Evolution
        try:
            from interface.evolution_menu import handle_system_evolution
            cls.register(
                name="evolution",
                handler=handle_system_evolution,
                title="Autonomous System Evolution",
                category=MenuCategory.EVOLUTION.value,
                description="Self-modifying codebase engine and prompt mutations",
                shortcut="8",
                icon="🧬",
            )
        except Exception:
            pass

        # 9. History
        try:
            from interface.history_menu import history_menu
            cls.register(
                name="history",
                handler=history_menu,
                title="Cross-Session History Ledger",
                category=MenuCategory.HISTORY.value,
                description="Audit logs, past session traces, mission output reports",
                shortcut="9",
                icon="📜",
            )
        except Exception:
            pass

        # 10. System
        try:
            from interface.system_menu import system_menu
            cls.register(
                name="system",
                handler=system_menu,
                title="System Health & Diagnostics",
                category=MenuCategory.SYSTEM.value,
                description="Hardware resource monitoring, process trees, and watchdog",
                shortcut="10",
                icon="🛡️",
            )
        except Exception:
            pass

        # 11. Personalize
        try:
            from interface.personalize import handle_personalize
            cls.register(
                name="personalize",
                handler=handle_personalize,
                title="User Preferences & Keys",
                category=MenuCategory.SETTINGS.value,
                description="Personalized user settings, API keys, theme switcher",
                shortcut="P",
                icon="👤",
            )
        except Exception:
            pass


MENU_REGISTRY = MenuRegistry


# ---------------------------------------------------------------------------
# Theme Registry
# ---------------------------------------------------------------------------

class ThemeRegistry:
    """Thread-safe registry for visual themes and color palettes."""

    _lock = threading.RLock()
    _themes: Dict[str, ThemePalette] = {}
    _engines: Dict[str, Type[BaseThemeEngine]] = {}
    _initialized_defaults: bool = False

    @classmethod
    def _ensure_defaults(cls) -> None:
        if cls._initialized_defaults:
            return
        with cls._lock:
            if cls._initialized_defaults:
                return
            cls._initialized_defaults = True
            defaults = [
                ThemePalette(name="claude", primary="plum1", secondary="plum1", border_style="plum1", focused_color="#00ffff"),
                ThemePalette(name="anthropic", primary="plum1", secondary="plum1", border_style="plum1", focused_color="#00ffff"),
                ThemePalette(name="minimalist", primary="white", secondary="dim", border_style="dim", focused_color="white"),
                ThemePalette(name="industrial", primary="orange3", secondary="magenta", border_style="orange3", focused_color="#ffbbff"),
                ThemePalette(name="matrix", primary="green", secondary="bold green", border_style="green", focused_color="#00ff00"),
                ThemePalette(name="neon", primary="bright_cyan", secondary="bright_magenta", border_style="bright_magenta", focused_color="#ff00ff"),
                ThemePalette(name="cyberpunk", primary="yellow", secondary="magenta", border_style="magenta", focused_color="#ffff00"),
                ThemePalette(name="dark", primary="dim", secondary="dim", border_style="dim", focused_color="white"),
            ]
            for t in defaults:
                cls._themes[t.name] = t

    @classmethod
    def register_theme(cls, theme: ThemePalette) -> None:
        with cls._lock:
            cls._themes[theme.name.lower()] = theme

    @classmethod
    def register_palette(cls, palette: ThemePalette, overwrite: bool = True) -> None:
        cls.register_theme(palette)

    @classmethod
    def register_engine(cls, name: str, engine_cls: Type[BaseThemeEngine], overwrite: bool = True) -> None:
        with cls._lock:
            cls._engines[name.lower()] = engine_cls

    @classmethod
    def get_theme(cls, name: str) -> ThemePalette:
        cls._ensure_defaults()
        with cls._lock:
            key = name.strip().lower()
            return cls._themes.get(key, cls._themes.get("claude", ThemePalette(name=name)))

    @classmethod
    def get_palette(cls, name: str) -> ThemePalette:
        return cls.get_theme(name)

    @classmethod
    def list_themes(cls) -> List[str]:
        cls._ensure_defaults()
        with cls._lock:
            return sorted(list(cls._themes.keys()))


THEME_REGISTRY = ThemeRegistry


# ---------------------------------------------------------------------------
# Telemetry & TUI Registry
# ---------------------------------------------------------------------------

class TelemetryRegistry:
    _collectors: Dict[str, Callable[[], Dict[str, Any]]] = {}

    @classmethod
    def register(cls, name: str, collector_fn: Callable[[], Dict[str, Any]]) -> None:
        cls._collectors[name.lower()] = collector_fn

    @classmethod
    def get(cls, name: str) -> Optional[Callable[[], Dict[str, Any]]]:
        return cls._collectors.get(name.lower())

    @classmethod
    def collect_all(cls) -> Dict[str, Any]:
        result = {}
        for name, fn in cls._collectors.items():
            try:
                result[name] = fn()
            except Exception:
                pass
        return result


class TUIAppRegistry:
    _apps: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, app_cls: Any) -> None:
        cls._apps[name.lower()] = app_cls

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        return cls._apps.get(name.lower())

    @classmethod
    def list_apps(cls) -> List[str]:
        return list(cls._apps.keys())


class InterfaceRegistry:
    menus = MENU_REGISTRY
    themes = THEME_REGISTRY
    telemetry = TelemetryRegistry
    apps = TUIAppRegistry


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def register_menu(
    name: Optional[Union[str, Callable[..., Any]]] = None,
    handler: Optional[Callable[..., Any]] = None,
    title: str = "",
    category: Union[MenuCategory, str] = "General",
    description: str = "",
    shortcut: Optional[str] = None,
    icon: str = "📌",
    badge: Optional[str] = None,
    is_async: bool = True,
    overwrite: bool = True,
    key: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    return MenuRegistry.register(
        name=name,
        handler=handler,
        title=title,
        category=category,
        description=description,
        shortcut=shortcut,
        icon=icon,
        badge=badge,
        is_async=is_async,
        overwrite=overwrite,
        key=key,
        **kwargs,
    )


def list_available_menus(category: Optional[Union[MenuCategory, str]] = None) -> List[MenuOption]:
    return MenuRegistry.list_menus(category=category)


def get_menu_info(key: str) -> Optional[MenuOption]:
    try:
        return MenuRegistry.get_menu(key)
    except Exception:
        return None


def list_available_themes() -> List[str]:
    return ThemeRegistry.list_themes()


def get_theme_palette(name: str) -> ThemePalette:
    return ThemeRegistry.get_theme(name)


__all__ = [
    "MenuOption",
    "MenuRegistry",
    "MENU_REGISTRY",
    "ThemeRegistry",
    "THEME_REGISTRY",
    "TelemetryRegistry",
    "TUIAppRegistry",
    "InterfaceRegistry",
    "register_menu",
    "list_available_menus",
    "get_menu_info",
    "list_available_themes",
    "get_theme_palette",
]
