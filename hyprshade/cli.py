import os
from datetime import datetime
from itertools import chain
from os import path
from typing import Annotated, Optional, cast

import typer
from more_itertools import quantify

from .constants import SHADER_DIRS
from .helpers import resolve_shader_path
from .hyprctl import clear_screen_shader, get_screen_shader, set_screen_shader
from .utils import systemd_user_config_home

app = typer.Typer(no_args_is_help=True)


@app.command()
def on(shader_name_or_path: Annotated[str, typer.Argument(show_default=False)]) -> int:
    """Turn on screen shader."""

    shader_path = resolve_shader_path(shader_name_or_path)
    return set_screen_shader(shader_path)


@app.command()
def off() -> int:
    """Turn off screen shader."""

    return clear_screen_shader()


def is_same_shader(s: str | None, s2: str | None) -> bool:
    if s is None or s2 is None:
        return False
    s, s2 = resolve_shader_path(s), resolve_shader_path(s2)
    return path.samefile(s, s2)


@app.command()
def toggle(
    shader_name_or_path: Annotated[
        Optional[str], typer.Argument(show_default=False)  # noqa: UP007
    ] = None,
    fallback: Annotated[
        Optional[str],  # noqa: UP007
        typer.Option(
            help="Shader to switch to instead of toggling off.",
            show_default=False,
            metavar="shader",
        ),
    ] = None,
    fallback_default: Annotated[
        bool,
        typer.Option(
            "--fallback-default",
            help="Use default shader as fallback. (see --fallback)",
            show_default=False,
        ),
    ] = False,
    fallback_auto: Annotated[
        bool,
        typer.Option(
            "--fallback-auto",
            help="Use currently scheduled shader as fallback."
            " (If the currently scheduled shader is SHADER_NAME_OR_PATH, the default"
            " shader will be used as the fallback instead.)",
            show_default=False,
        ),
    ] = False,
) -> int:
    """Toggle screen shader.

    If run with no arguments, SHADER_NAME_OR_PATH is inferred based on schedule.

    When --fallback is specified, will toggle between SHADER_NAME_OR_PATH and the
    fallback shader. --fallback-default will toggle between SHADER_NAME_OR_PATH and the
    default shader, whereas --fallback-auto will toggle between SHADER_NAME_OR_PATH and
    the currently scheduled shader. (--fallback-auto is equivalent to --fallback-default
    if the currently scheduled shader is SHADER_NAME_OR_PATH.)
    """

    from .config import Config

    fallback_opts = [fallback, fallback_default, fallback_auto]
    if quantify(fallback_opts) > 1:
        raise typer.BadParameter("Cannot specify more than 1 --fallback* option")

    t = datetime.now().time()
    schedule = Config().to_schedule()
    scheduled_shade = schedule.find_shade(t)
    current_shader = get_screen_shader()

    shade = shader_name_or_path or scheduled_shade

    if fallback_default or (fallback_auto and is_same_shader(shade, scheduled_shade)):
        fallback = schedule.default_shade_name
    elif fallback_auto:
        fallback = scheduled_shade
    toggle_off = off if fallback is None else lambda: on(cast(str, fallback))

    if is_same_shader(shade, current_shader):
        return toggle_off()
    if shade is not None:
        return on(shade)

    return 0


@app.command()
def auto() -> int:
    """Turn on/off screen shader based on schedule."""

    from .config import Config

    t = datetime.now().time()
    shade = Config().to_schedule().find_shade(t)

    if shade is not None:
        return on(shade)
    return off()


@app.command()
def install() -> int:
    """Install systemd user units."""

    from .config import Config

    schedule = Config().to_schedule()

    with open(path.join(systemd_user_config_home(), "hyprshade.service"), "w") as f:
        f.write(
            """[Unit]
Description=Apply screen filter

[Service]
Type=oneshot
ExecStart="/usr/bin/hyprshade" auto"""
        )

    with open(path.join(systemd_user_config_home(), "hyprshade.timer"), "w") as f:
        on_calendar = "\n".join(
            sorted([f"OnCalendar=*-*-* {x}" for x in schedule.on_calendar_entries()])
        )
        f.write(
            f"""[Unit]
Description=Apply screen filter on schedule

[Timer]
{on_calendar}

[Install]
WantedBy=timers.target"""
        )

    return 0


@app.command()
def ls() -> int:
    """List available screen shaders."""

    current_shader = get_screen_shader()
    shader_base = path.basename(current_shader) if current_shader else None

    for shader in chain(
        *map(
            os.listdir,
            SHADER_DIRS,
        )
    ):
        c = "*" if shader == shader_base else " "
        shader, _ = path.splitext(shader)
        print(f"{c} {shader}")

    return 0


def main():
    return app()
