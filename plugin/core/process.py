from .logging import debug, exception_log, server_log
import subprocess
import os
import threading


def start_server(server_binary_args, working_dir, env):
    debug("starting " + str(server_binary_args))
    si = None
    if os.name == "nt":
        si = subprocess.STARTUPINFO()  # type: ignore
        si.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW  # type: ignore
    try:
        return subprocess.Popen(
            server_binary_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
            env=env,
            startupinfo=si)

    except Exception as err:
        # sublime.status_message("Failed to start SublimeCodeIntel server {}".format(str(server_binary_args)))
        exception_log("Failed to start server", err)


def attach_logger(process, stream):
    threading.Thread(target=lambda: log_stream(process, stream)).start()


def log_stream(process, stream):
    """
    Reads any errors from the SublimeCodeIntel process.
    """
    running = True
    while running:
        running = process.poll() is None

        try:
            content = stream.readline()
            if not content:
                break
            try:
                decoded = content.decode("UTF-8")
            except UnicodeDecodeError:
                decoded = content
            server_log(decoded.strip())
        except IOError as err:
            exception_log("Failure reading stream", err)
            return

    debug("SublimeCodeIntel stream logger stopped.")
