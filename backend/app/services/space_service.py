"""Space (tenant) service for multi-subdomain support."""

from pathlib import Path

import yaml
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class SpaceTheme(BaseModel):
    """Theme configuration for a space."""

    primary: str = "195 80% 45%"
    primary_foreground: str = "0 0% 100%"
    secondary: str = "45 80% 55%"
    secondary_foreground: str = "222.2 47.4% 11.2%"
    background: str = "0 0% 100%"
    foreground: str = "222.2 84% 4.9%"
    card: str = "0 0% 100%"
    card_foreground: str = "222.2 84% 4.9%"
    popover: str = "0 0% 100%"
    popover_foreground: str = "222.2 84% 4.9%"
    muted: str = "210 40% 96.1%"
    muted_foreground: str = "215.4 16.3% 46.9%"
    accent: str = "210 40% 96.1%"
    accent_foreground: str = "222.2 47.4% 11.2%"
    destructive: str = "0 84.2% 60.2%"
    destructive_foreground: str = "210 40% 98%"
    border: str = "214.3 31.8% 91.4%"
    input: str = "214.3 31.8% 91.4%"
    ring: str = "195 80% 45%"


class Space(BaseModel):
    """Space configuration."""

    id: str
    name: str
    tagline: str = ""
    description: str = ""
    domain: str = ""
    footer_text: str = ""
    theme: SpaceTheme = SpaceTheme()
    design_filter: str = "all"
    logo_url: str | None = None
    design_tips: list[str] = []


class SpaceService:
    """Service for loading and resolving spaces."""

    def __init__(self):
        self.spaces_path = Path(settings.spaces_path)
        self._cache: dict[str, Space] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._load_all()
        self._loaded = True

    def _load_all(self):
        if not self.spaces_path.exists():
            return
        for space_dir in self.spaces_path.iterdir():
            if not space_dir.is_dir():
                continue
            config_path = space_dir / "space.yaml"
            if not config_path.exists():
                continue
            try:
                with open(config_path) as f:
                    data = yaml.safe_load(f)
                space = Space(**data)
                self._cache[space.id] = space
            except Exception:
                continue

    def get_space(self, space_id: str) -> Space | None:
        """Get a space by its ID."""
        self._ensure_loaded()
        return self._cache.get(space_id)

    def get_default(self) -> Space:
        """Get the default space."""
        self._ensure_loaded()
        return self._cache.get(
            "default",
            Space(id="default", name="rSwag", domain="rswag.online"),
        )

    def list_spaces(self) -> list[Space]:
        """List all spaces."""
        self._ensure_loaded()
        return list(self._cache.values())

    def clear_cache(self):
        """Clear the cache to force reload."""
        self._cache.clear()
        self._loaded = False
