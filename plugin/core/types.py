class Settings(object):

    def __init__(self):
        self.show_status_messages = True
        self.show_view_status = True
        self.auto_show_diagnostics_panel = True
        self.show_diagnostics_phantoms = False
        self.show_diagnostics_count_in_view_status = False
        self.show_diagnostics_in_view_status = True
        self.show_diagnostics_severity_level = 3
        self.only_show_lsp_completions = False
        self.diagnostics_highlight_style = "underline"
        self.highlight_active_signature_parameter = True
        self.document_highlight_style = "stippled"
        self.document_highlight_scopes = {
            "unknown": "text",
            "text": "text",
            "read": "markup.inserted",
            "write": "markup.changed"
        }
        self.diagnostics_gutter_marker = "dot"
        self.complete_all_chars = False
        self.completion_hint_type = "auto"
        self.resolve_completion_for_snippets = False
        self.log_debug = True
        self.log_server = True
        self.log_stderr = False
        self.log_payloads = False


class ClientStates(object):
    STARTING = 0
    READY = 1
    STOPPING = 2


class ConfigState(object):

    def __init__(self, project_path, state=ClientStates.STARTING, client=None, capabilities=None):
        self.project_path = project_path
        self.state = state
        self.client = client
        self.capabilities = capabilities


class ClientConfig(object):
    def __init__(self, name, binary_args, tcp_port, scopes, syntaxes, languageId,
                 enabled=True, init_options=dict(), settings=dict(), env=dict()):
        self.name = name
        self.binary_args = binary_args
        self.tcp_port = tcp_port
        self.scopes = scopes
        self.syntaxes = syntaxes
        self.languageId = languageId
        self.enabled = enabled
        self.init_options = init_options
        self.settings = settings
        self.env = env

    def apply_settings(self, settings: dict) -> None:
        if "command" in settings:
            self.binary_args = settings.get("command", [])
        if "tcp_port" in settings:
            self.tcp_port = settings.get("tcp_port", None)
        if "scopes" in settings:
            self.scopes = settings.get("scopes", [])
        if "syntaxes" in settings:
            self.syntaxes = settings.get("syntaxes", [])
        if "languageId" in settings:
            self.languageId = settings.get("languageId", "")
        if "enabled" in settings:
            self.enabled = settings.get("enabled", True)
        if "initializationOptions" in settings:
            self.init_options = settings.get("initializationOptions", dict())
        if "settings" in settings:
            self.settings = settings.get("settings", dict())
        if "env" in settings:
            self.env = settings.get("env", dict())

    def get_settings(self, window):
        return self.settings

    def get_language_id(self, view):
        return self.languageId
