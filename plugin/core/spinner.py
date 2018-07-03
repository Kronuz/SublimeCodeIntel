import sublime


class Spinner(object):
    spinners = {
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
            sublime.status_message(frames[self.frame])
        else:
            sublime.status_message("")

    def start(self, spinner):
        key = self.key = self.key + 1
        sublime.set_timeout_async(lambda: self.stop(key), 1000)
        if self.enabled:
            self.enabled = spinner
        else:
            self.enabled = spinner
            self.animate()

    def stop(self, key):
        if self.key == key:
            self.key = 0
            self.enabled = False
