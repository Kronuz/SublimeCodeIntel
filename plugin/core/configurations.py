import re
import sublime

from .settings import ClientConfig, client_configs
from .logging import debug
from .workspace import get_project_config

assert ClientConfig

try:
    from typing import Any, List, Dict, Tuple, Callable, Optional
    assert Any and List and Dict and Tuple and Callable and Optional
except ImportError:
    pass


window_client_configs = dict()  # type: Dict[int, List[ClientConfig]]


def _get_scope_client_config(view: 'sublime.View', configs: 'List[ClientConfig]') -> 'Tuple[Optional[ClientConfig], int]':
    # When there are multiple server configurations, all of which are for
    # similar scopes (e.g. 'source.json', 'source.json.sublime.settings') the
    # configuration with the most specific scope (highest ranked selector)
    # in the current position is preferred.
    scope_client_config = None
    scope_score = 0
    sel = view.sel()
    if len(sel) > 0:
        pos = sel[0].begin()
        for config in configs:
            for scope in config.scopes:
                score = view.score_selector(pos, scope)
                if score > scope_score:
                    scope_score = score
                    scope_client_config = config
    return scope_client_config, scope_score


def get_scope_client_config(view: 'sublime.View', configs: 'List[ClientConfig]') -> 'Optional[ClientConfig]':
    return _get_scope_client_config(view, configs)[0]


def register_client_config(config: ClientConfig) -> None:
    window_client_configs.clear()
    client_configs.add_external_config(config)


def get_global_client_config(view: sublime.View) -> 'Optional[ClientConfig]':
    return get_scope_client_config(view, client_configs.all)


def get_default_client_config(view: sublime.View) -> 'Optional[ClientConfig]':
    return get_scope_client_config(view, client_configs.defaults)


def get_window_client_config(view: sublime.View) -> 'Optional[ClientConfig]':
    window = view.window()
    if window:
        configs_for_window = window_client_configs.get(window.id(), [])
        return get_scope_client_config(view, configs_for_window)
    else:
        return None


def config_for_scope(view: sublime.View) -> 'Optional[ClientConfig]':
    # check window_client_config first
    window = view.window()
    if window:
        configs_for_window = window_client_configs.get(window.id(), [])
        window_client_config, window_score = _get_scope_client_config(view, configs_for_window)
    else:
        window_client_config, window_score = None, 0
    global_client_config, global_score = _get_scope_client_config(view, client_configs.all)
    if not window_client_config or global_score > window_score:
        if global_client_config:
            if window:
                window_client_config = apply_window_settings(global_client_config, view)
                add_window_client_config(window, window_client_config)
                return window_client_config
            else:
                # always return a client config even if the view has no window anymore
                return global_client_config

    return window_client_config


def add_window_client_config(window: 'sublime.Window', config: 'ClientConfig'):
    global window_client_configs
    window_client_configs.setdefault(window.id(), []).append(config)


def clear_window_client_configs(window: 'sublime.Window'):
    global window_client_configs
    if window.id() in window_client_configs:
        del window_client_configs[window.id()]


def apply_window_settings(client_config: 'ClientConfig', view: 'sublime.View') -> 'ClientConfig':
    window = view.window()
    if window:
        window_config = get_project_config(window)

        if client_config.name in window_config:
            overrides = window_config[client_config.name]
            debug('window has override for', client_config.name, overrides)
            return ClientConfig(
                client_config.name,
                overrides.get("command", client_config.binary_args),
                overrides.get("tcp_port", client_config.tcp_port),
                overrides.get("scopes", client_config.scopes),
                overrides.get("syntaxes", client_config.syntaxes),
                overrides.get("languageId", client_config.languageId),
                overrides.get("enabled", client_config.enabled),
                overrides.get("initializationOptions", client_config.init_options),
                overrides.get("settings", client_config.settings),
                overrides.get("env", client_config.env)
            )

    return client_config


def is_supportable_syntax(syntax: str) -> bool:
    # TODO: filter out configs disabled by the user.
    for config in client_configs.defaults:
        if re.search(r'|'.join(r'\b%s\b' % re.escape(s) for s in config.syntaxes), syntax, re.IGNORECASE):
            return True
    return False


def is_supported_syntax(syntax: str) -> bool:
    for config in client_configs.all:
        if re.search(r'|'.join(r'\b%s\b' % re.escape(s) for s in config.syntaxes), syntax, re.IGNORECASE):
            return True
    return False


def is_supported_view(view: sublime.View) -> bool:
    # TODO: perhaps make this check for a client instead of a config
    if config_for_scope(view):
        return True
    else:
        return False
