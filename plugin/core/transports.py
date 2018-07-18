import re
from queue import Queue
from abc import ABCMeta, abstractmethod
import threading
import time
import socket
from .logging import exception_log, server_log, debug


CONTENT_LENGTH_RE = re.compile(br'Content-Length:\s*(\d+)', re.IGNORECASE)
TCP_CONNECT_TIMEOUT = 5


class Transport(object, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def start(self, on_receive, on_closed):
        pass

    @abstractmethod
    def send(self, message):
        pass


STATE_HEADERS = 0
STATE_CONTENT = 1


def start_tcp_transport(port):
    host = "localhost"
    start_time = time.time()
    debug('connecting to {}:{}'.format(host, port))

    while time.time() - start_time < TCP_CONNECT_TIMEOUT:
        try:
            sock = socket.create_connection((host, port))
            return TCPTransport(sock)
        except ConnectionRefusedError:
            pass

    # process.kill()
    raise Exception("Timeout connecting to socket")


class TCPTransport(Transport):
    def __init__(self, socket):
        self.socket = socket

    def start(self, on_receive, on_closed):
        self.on_receive = on_receive
        self.on_closed = on_closed
        self.queue = Queue()
        self.read_thread = threading.Thread(target=self.read_socket)
        self.read_thread.start()
        self.write_thread = threading.Thread(target=self.write_socket)
        self.write_thread.start()

    def close(self):
        self.queue.put(None)
        socket = self.socket
        if socket:
            socket.close()
        self.socket = None
        self.on_closed()

    def read_socket(self):
        remaining_data = b""
        read_state = STATE_HEADERS
        content_length = 0
        socket = self.socket
        while socket:
            try:
                if self.socket is not socket:
                    raise IOError("Closed socket")
                received_data = socket.recv(4096)
            except Exception as err:
                exception_log("Failure reading from socket", err)
                self.close()
                break

            if not received_data:
                debug("no data received, closing")
                self.close()
                break

            data = remaining_data + received_data
            remaining_data = b""

            is_incomplete = False
            while len(data) > 0 and not is_incomplete:
                if read_state == STATE_HEADERS:
                    headers, _sep, rest = data.partition(b"\r\n\r\n")
                    if len(_sep) < 1:
                        is_incomplete = True
                        remaining_data = data
                    else:
                        for header in headers.split(b"\r\n"):
                            match = CONTENT_LENGTH_RE.match(header)
                            if match:
                                content_length = int(match.group(1))
                                read_state = STATE_CONTENT
                        data = rest

                if read_state == STATE_CONTENT:
                    # read content bytes
                    if len(data) >= content_length:
                        content = data[:content_length]
                        self.on_receive(content.decode("UTF-8"))
                        data = data[content_length:]
                        read_state = STATE_HEADERS
                    else:
                        is_incomplete = True
                        remaining_data = data

    def write_socket(self):
        socket = self.socket
        while socket:
            message = self.queue.get()
            if message is None:
                self.close()
                break
            try:
                if self.socket is not socket:
                    raise IOError("Closed socket")
                debug('socket send')
                socket.sendall(bytes(message, 'UTF-8'))
            except Exception as err:
                self.close()
                exception_log("Failure writing to stdin", err)
                break

        debug("SublimeCodeIntel stdin thread ended.")

    def send(self, message):
        self.queue.put(message)


class StdioTransport(Transport):
    def __init__(self, process):
        self.process = process

    def start(self, on_receive, on_closed):
        self.on_receive = on_receive
        self.on_closed = on_closed
        self.queue = Queue()
        self.stdout_thread = threading.Thread(target=self.read_stdout)
        self.stdout_thread.start()
        self.stdin_thread = threading.Thread(target=self.write_stdin)
        self.stdin_thread.start()

    def close(self):
        self.queue.put(None)
        process = self.process
        if process:
            process.stdin.close()
            process.stdout.close()
        self.process = None
        self.on_closed()

    def read_stdout(self):
        """
        Reads JSON responses from process and dispatch them to response_handler
        """
        process = self.process
        while process and process.poll() is None:
            try:
                content_length = 0

                while True:
                    if self.process is not process:
                        raise IOError("Closed process")
                    header = process.stdout.readline()
                    if not header:
                        raise IOError("Closed stream")
                    header = header.strip()
                    if not header:
                        # End of headers, break
                        break
                    match = CONTENT_LENGTH_RE.match(header)
                    if match:
                        content_length = int(match.group(1))

                if not content_length:
                    continue

                content = process.stdout.read(content_length)

            except Exception as err:
                self.close()
                exception_log("Failure reading stdout", err)
                break

            self.on_receive(content.decode("UTF-8"))

        debug("SublimeCodeIntel stdout thread ended.")

    def write_stdin(self):
        process = self.process
        while process and process.poll() is None:
            message = self.queue.get()
            if message is None:
                self.close()
                break
            message = bytes(message, 'UTF-8')
            try:
                process.stdin.write(message)
                process.stdin.flush()
            except Exception as err:
                self.close()
                exception_log("Failure writing to stdin", err)
                break

        debug("SublimeCodeIntel stdin thread ended.")

    def send(self, message):
        self.queue.put(message)
