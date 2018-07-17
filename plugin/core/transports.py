from abc import ABCMeta, abstractmethod
import threading
import time
import socket
from .logging import exception_log, debug

ContentLengthHeader = b"Content-Length: "
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
        except ConnectionRefusedError as e:
            pass

    # process.kill()
    raise Exception("Timeout connecting to socket")


class TCPTransport(Transport):
    def __init__(self, socket):
        self.socket = socket

    def start(self, on_receive, on_closed):
        self.on_receive = on_receive
        self.on_closed = on_closed
        self.read_thread = threading.Thread(target=self.read_socket)
        self.read_thread.start()

    def close(self):
        self.socket = None
        self.on_closed()

    def read_socket(self):
        remaining_data = b""
        is_incomplete = False
        read_state = STATE_HEADERS
        content_length = 0
        while self.socket:
            is_incomplete = False
            try:
                received_data = self.socket.recv(4096)
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

            while len(data) > 0 and not is_incomplete:
                if read_state == STATE_HEADERS:
                    headers, _sep, rest = data.partition(b"\r\n\r\n")
                    if len(_sep) < 1:
                        is_incomplete = True
                        remaining_data = data
                    else:
                        for header in headers.split(b"\r\n"):
                            if header.startswith(ContentLengthHeader):
                                header_value = header[len(ContentLengthHeader):]
                                content_length = int(header_value)
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

    def send(self, message):
        try:
            if self.socket:
                debug('socket send')
                self.socket.sendall(bytes(message, 'UTF-8'))
        except Exception as err:
            exception_log("Failure writing to socket", err)
            self.socket = None
            self.on_closed()


class StdioTransport(Transport):
    def __init__(self, process):
        self.process = process

    def start(self, on_receive, on_closed):
        self.on_receive = on_receive
        self.on_closed = on_closed
        self.lock = threading.Lock()
        self.stdout_thread = threading.Thread(target=self.read_stdout)
        self.stdout_thread.start()

    def close(self):
        self.process = None
        self.on_closed()

    def read_stdout(self):
        """
        Reads JSON responses from process and dispatch them to response_handler
        """
        ContentLengthHeader = b"Content-Length: "

        running = True
        while running:
            running = self.process.poll() is None

            try:
                content_length = 0
                while self.process:
                    header = self.process.stdout.readline()
                    if header:
                        header = header.strip()
                    if not header:
                        break
                    if header.startswith(ContentLengthHeader):
                        content_length = int(header[len(ContentLengthHeader):])

                if (content_length > 0):
                    content = self.process.stdout.read(content_length)

                    self.on_receive(content.decode("UTF-8"))

            except IOError as err:
                self.close()
                exception_log("Failure reading stdout", err)
                break

        debug("LSP stdout process ended.")

    def send(self, message):
        if self.process:
            try:
                with self.lock:
                    self.process.stdin.write(bytes(message, 'UTF-8'))
                    self.process.stdin.flush()
            except (BrokenPipeError, OSError) as err:
                exception_log("Failure writing to stdout", err)
                self.close()
