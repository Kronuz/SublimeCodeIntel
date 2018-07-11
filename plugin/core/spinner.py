import sublime


class Spinner(object):
    # From https://github.com/ManrajGrover/py-spinners/blob/master/spinners/spinners.py
    spinners = {
        "default": {
            "interval": 100,
            "frames": [
                "◐",
                "◓",
                "◑",
                "◒",
            ],
        },
        "dots": {
            "interval": 80,
            "frames": [
                "⠋",
                "⠙",
                "⠹",
                "⠸",
                "⠼",
                "⠴",
                "⠦",
                "⠧",
                "⠇",
                "⠏",
            ],
        },
        "line": {
            "interval": 130,
            "frames": [
                "-",
                "\\",
                "|",
                "/",
            ],
        },
        "bouncingBall": {
            "interval": 80,
            "frames": [
                "( ●    )",
                "(  ●   )",
                "(   ●  )",
                "(    ● )",
                "(     ●)",
                "(    ● )",
                "(   ●  )",
                "(  ●   )",
                "( ●    )",
                "(●     )",
            ],
        },
        "point": {
            "interval": 125,
            "frames": [
                "∙∙∙",
                "●∙∙",
                "∙●∙",
                "∙∙●",
                "∙∙∙",
            ],
        },
        "fire": {
            "interval": 60,
            "frames": [
                "🔥 ",
                "🔥 ",
                "🔥 ",
                "🔥 ",
                "🔥 ",
                "🔥 ",
                " ",
            ],
        },
        "monkey": {
            "interval": 300,
            "frames": [
                "🙈 ",
                "🙈 ",
                "🙉 ",
                "🙊 ",
            ],
        },
        "earth": {
            "interval": 180,
            "frames": [
                "🌍 ",
                "🌎 ",
                "🌏 ",
            ],
        },
        "clock": {
            "interval": 100,
            "frames": [
                "🕛 ",
                "🕐 ",
                "🕑 ",
                "🕒 ",
                "🕓 ",
                "🕔 ",
                "🕕 ",
                "🕖 ",
                "🕗 ",
                "🕘 ",
                "🕙 ",
                "🕚 "
            ]
        },
        "moon": {
            "interval": 80,
            "frames": [
                "🌑 ",
                "🌒 ",
                "🌓 ",
                "🌔 ",
                "🌕 ",
                "🌖 ",
                "🌗 ",
                "🌘 ",
            ],
        },
    }

    def __init__(self):
        self.key = 0
        self.frame = 0
        self.enabled = False

    def animate(self):
        if self.enabled:
            spinner = self.spinners[self.enabled]
            interval = spinner['interval']
            frames = spinner['frames']
            sublime.set_timeout_async(self.animate, interval)
            self.frame = (self.frame + 1) % len(frames)
            sublime.status_message(self.prefix + " " + frames[self.frame] + " " + self.suffix)

    def deanimate(self, key):
        if self.key == key:
            self.stop()

    def start(self, prefix="", suffix="", timeout=1000, spinner='default'):
        key = self.key = self.key + 1
        self.prefix = prefix
        self.suffix = suffix
        animated, self.enabled = self.enabled, spinner
        if not animated:
            self.animate()
        if timeout > 0:
            sublime.set_timeout_async(lambda: self.deanimate(key), timeout)

    def stop(self, prefix="", suffix=""):
        self.key = 0
        self.prefix = prefix
        self.suffix = suffix
        animated, self.enabled = self.enabled, False
        if animated:
            sublime.status_message(self.prefix + " " + self.suffix)


spinner = Spinner()
