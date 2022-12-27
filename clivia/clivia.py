import argparse
import shlex
import sys, io
import uselect as select
import socket
import builtins
from micropython import const

class CliviaSession:
    def __init__(self, stream_in, stream_in_name:str, stream_out, stream_out_name:str, perm_lvl:int):
        self.stream_in = stream_in
        self.stream_out = stream_out
        self.stream_in_name = stream_in_name
        self.stream_out_name = stream_out_name
        self.close_in = False
        self.close_out = False
        self.return_handler = CliviaSession.empty_return_handler
        self.perm_lvl = perm_lvl
        self.cache = object()
        self.echo_enabled = False
        self.echo_format = '{}'
        self.closed = False

    def open(self):
        pass

    def close(self):
        if self.close_in:
            self.stream_in.close()
        
        if self.close_out:
            self.stream_out.close()
        
        self.closed = True

    def set_echo(self, enabled, echo_format=None):
        self.echo_enabled = enabled
        if echo_format is not None:
            self.echo_format = echo_format

    def echo(self, line):
        print = Clivia.print_to_stream(self.stream_out)
        
        line = line.strip()
        if self.echo_enabled and len(line) > 0:
            print(self.echo_format.format(line))

    @staticmethod
    def empty_return_handler(cmdin:str, retval, print=builtins.print) -> None: pass

class Clivia:
    STREAM_CLOSED = const(0)
    STREAM_IN = const(1)
    STREAM_OUT = const(2)
    STREAM_IO = const(3)
    OPERATOR_IN = const('<<')
    OPERATOR_OUT = const('>>')

    def __init__(self):
        self.in_streams  : dict[str, io.IOBase]     = {}   # name: stream object
        self.out_streams : dict[str, io.IOBase]     = {}   # name: stream object
        self.sessions    : dict[str, CliviaSession] = {}   # sin name: session object (sout name, permlvl, cache)
        self.parsers     : dict[str, argparse.ArgumentParser] = {}   # command: ArgumentParser
        self.commands    : dict[str, (function, int)] = {} # command: (func, permlvl)
        self.select_timeout = 0.5
    
    def __enter__(self):
        pass
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        for session in self.sessions.values():
            self.close_session(session.stream_in_name)

    def mount_stream(self, name, stream, mode):
        if mode == Clivia.STREAM_IN or mode == Clivia.STREAM_IO:
            self.in_streams[name] = stream
        if mode == Clivia.STREAM_OUT or mode == Clivia.STREAM_IO:
            self.out_streams[name] = stream

    def get_stream(self, name):
        is_input = name in self.in_streams.keys()
        is_output = name in self.out_streams.keys()

        if is_input and is_output:
            return self.in_streams[name], Clivia.STREAM_IO
        
        if is_input:
            return self.in_streams[name], Clivia.STREAM_IN
        
        if is_output:
            return self.out_streams[name], Clivia.STREAM_OUT
        
        return None, Clivia.STREAM_CLOSED

    def register_session(self, session: CliviaSession):
        self.sessions[session.stream_in_name] = session
        self.mount_stream(session.stream_out_name, session.stream_out, Clivia.STREAM_OUT)
        self.mount_stream(session.stream_in_name, session.stream_in, Clivia.STREAM_IN)

    def add_command(self, command, func, parser: argparse.ArgumentParser, perm_lvl = 0):
        self.parsers[command] = parser
        self.commands[command] = (func, perm_lvl)

    def loop(self):
        readers, _, _ = select.select(list(self.in_streams.values()), [], [], self.select_timeout)
        for reader in readers:
            # rewrite this
            stream_in_name, stream = [(key, value) for key, value in self.in_streams.items() if value == reader][0]

            line = stream.readline()
            if type(line) is bytes: line = line.decode('utf-8')
            if len(line.strip()) == 0: continue
            
            words = shlex.split(line)

            if (Clivia.OPERATOR_IN in words) and (Clivia.OPERATOR_OUT in words):
                raise ValueError # other error here

            if Clivia.OPERATOR_IN in words: # refactor this to allow multiple streams?
                stream_in_name = words.pop()
                operator = words.pop()
                if operator != Clivia.OPERATOR_IN:
                    raise ValueError # todo other error here
                if stream_in_name not in self.in_streams.keys():
                    raise KeyError # todo other error here
            
            session = self.sessions[stream_in_name]
            session.echo(line)
            
            if Clivia.OPERATOR_OUT in words:
                stream_out_name = words.pop()
                operator = words.pop()
                if operator != Clivia.OPERATOR_OUT:
                    raise ValueError # todo other error here
                if stream_out_name not in self.out_streams.keys():
                    raise KeyError # todo other error here
            else:
                stream_out_name = session.stream_out_name
            
            stream_out = self.out_streams[stream_out_name]

            command = words.pop(0)
            if command not in self.commands.keys():
                raise KeyError # todo other error here
            
            # special system commands
            if command == 'exit':
                self.close_session(stream_in_name) # self.close_session(session) ??
                continue

            func, perm_lvl = self.commands[command]
            if perm_lvl > session.perm_lvl:
                raise PermissionError # todo other error here
            
            parser = self.parsers[command]
            try:
                args = parser.parse_args(words, print=print)
            except Exception as exc:
                sys.print_exception(exc)
                raise ValueError # todo other error here

            try:
                kwargs = {"print": Clivia.print_to_stream(stream_out)}
                for field in dir(args):
                    if field is '__class__': continue # refactor this
                    kwargs[field] = getattr(args, field)
                retval = func(**kwargs)
            except Exception as exc:
                sys.print_exception(exc)
                raise RuntimeError # todo other error here
            
            try:
                session.return_handler(line, retval, print=print)
            except Exception as exc:
                raise RuntimeError # todo other error here

    def close_session(self, stream_in_name):
        session = self.sessions[stream_in_name]
        self.sessions.pop(stream_in_name)
        session.close()
        self.in_streams.pop(stream_in_name)
        self.out_streams.pop(session.stream_out_name)
        
    @staticmethod
    def print_to_stream(stream_out):        
        def _print(*args, **kwargs):
            kwargs["file"] = stream_out
            builtins.print(*args, **kwargs)
        return _print

class CliviaFile(CliviaSession):
    def __init__(self, input_filename, output_filename, output_mode='w', perm_lvl=0):
        super().__init__(
            open(input_filename, 'r'),           f"file/{input_filename}/in",
            open(output_filename, output_mode),  f"file/{output_filename}/out",
            perm_lvl)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.close_in = True
        self.close_out = True

class CliviaUSB(CliviaSession):
    def __init__(self, perm_lvl=0):
        super().__init__(
            sys.stdin,  'usb/in',
            sys.stdout, 'usb/out',
            perm_lvl)

class CliviaTCPClient(CliviaSession):
    def __init__(self, server_ip, port, blocking=False, perm_lvl=0):
        self.server_ip = server_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(blocking)
        self.connect()
        super().__init__(
            self.socket, f"tcpc/{server_ip}/in",
            self.socket, f"tcpc/{server_ip}/out",
            perm_lvl)
        self.close_in = True
    def connect(self):
        try:
            self.socket.connect((self.server_ip, self.port))
        except OSError as e:
            if e.args[0] not in [errno.EINPROGRESS, errno.ETIMEDOUT]:
                print('Error connecting', e) # todo change this

class CliviaTCPServerSession(CliviaSession):
    def __init__(self, client_ip, port, socket, perm_lvl=0):
        self.client_ip = client_ip
        self.port = port
        self.socket = socket
        super().__init__(
            self.socket, f"tcps/{client_ip}/in",
            self.socket, f"tcps/{client_ip}/out",
            perm_lvl)
        self.close_in = True

class CliviaTCPServer():
    def __init__(self, ip, port, blocking=False, perm_lvl=0):
        self.ip = ip
        self.port = port
        self.perm_lvl = perm_lvl
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        self.socket.setblocking(blocking)
    
    def accept_clients(self, cli):        
        try:
            tcp = self.socket.accept()
            if tcp is not None:
                conn, addr = tcp
                client_ip, port = addr
                session = CliviaTCPServerSession(client_ip, port, conn, perm_lvl=self.perm_lvl)
                cli.register_session(session)
        except OSError as exc:
            if exc.errno == errno.EAGAIN: pass
