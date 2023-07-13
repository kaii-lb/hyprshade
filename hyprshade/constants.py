from os import path
from typing import Final

from hyprshade.utils import hypr_config_home

EMPTY_STR: Final = "[[EMPTY]]"

_SYSTEM_SHADERS_DIR = "/usr/share/hyprshade/shaders"
SYSTEM_SHADERS_DIR: Final = (
    _SYSTEM_SHADERS_DIR if path.isdir(_SYSTEM_SHADERS_DIR) else None
)

_USER_SHADERS_DIR = path.join(hypr_config_home(), "shaders")
USER_SHADERS_DIR: Final = _USER_SHADERS_DIR if path.isdir(_USER_SHADERS_DIR) else None

SHADER_DIRS: Final = [
    x for x in [SYSTEM_SHADERS_DIR, USER_SHADERS_DIR] if x is not None
]
