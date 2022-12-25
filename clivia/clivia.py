import sys
import socket

class Clivia:
    def __init__(self, select_timeout=0.5):
        self.select_timeout = select_timeout
    

class CliviaSessionBase:
    def __init__(self):
        pass

class CliviaStream(CliviaSessionBase):
    def __init__(self, stream_in, stream_out=None):
        super().__init__()
        self.stream_in = stream_in
        self.stream_out = stream_in if (stream_out is None) else stream_out

class CliviaFile(CliviaStream):
    def __init__(self, input, output, output_mode='w'):
        super().__init__(
            open(input, 'r'),
            open(output, output_mode))
        self.input_filename = input
        self.output_filename = output

class CliviaUSB(CliviaStream):
    def __init__(self):
        super().__init__(sys.stdin, sys.stdout)

class CliviaTCPClient(CliviaStream):
    def __init__(self, server_ip, port, blocking=False):
        self.server_ip = server_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(blocking)
        self.socket.connect((self.server_ip, self.port))
        super().__init__(self.socket)

class CliviaTCPServer(CliviaSessionBase):
    def __init__(self, ip, port, blocking=False):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        self.socket.setblocking(blocking)
        super().__init__()
    def accept_clients(self):        
        try:
            tcp = self.socket.accept()
            if tcp is not None:
                conn, addr = tcp

                cli.add_session(CLISession(conn, conn, echo = True, echo_format = "#{}"))
        except OSError as exc:
            if exc.errno == errno.EAGAIN: pass


class argparse:
    class ArgumentParser:
        def __init__(self):
            pass

