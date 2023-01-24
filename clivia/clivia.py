import argparse
import shlex
import sys, io
import uselect as select
import socket
import builtins
import random
from micropython import const

class CliviaSession:
    def __init__(self, name, stdin, stdout):
        self.name = name
        self.stdin = stdin
        self.stdout = stdout
        self.close_in = False
        self.close_out = False
        self.echo_enabled = False
        self.echo_format = '{}'
        #self.return_handler = CliviaSession.empty_return_handler

    def open(self):
        return True

    def close(self):
        if self.close_in:  self.stdin.close()
        if self.close_out: self.stdout.close()
    
    def readline(self):
        return self.stdin.readline()

    def set_echo(self, enabled, echo_format=None):
        self.echo_enabled = enabled
        if echo_format is not None:
            self.echo_format = echo_format

    def echo(self, input_line):
        input_line = input_line.strip()
        if self.echo_enabled and len(input_line) > 0:
            self.print(self.echo_format.format(input_line))


class Clivia:
    SESSION_ID_COUNTER = 0
    OPERATOR_REDIRECT_OUT = const('>')

    def __init__(self):
        self.sessions    : dict[str, CliviaSession] = {}   # name: session object (name, permlvl, cache)
        self.parsers     : dict[str, argparse.ArgumentParser] = {}   # command: ArgumentParser
        self.commands    : dict[str, (function, int)] = {} # command: (func, permlvl)
    
    def __enter__(self):
        for session in self.sessions.values():
            session.open()
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        for session in self.sessions.values():
            self.remove_session(session.name)

    def register_session(self, session: CliviaSession):
        self.sessions[session.name] = session
    
    def add_command(self, command, func, parser: argparse.ArgumentParser):
        self.parsers[command] = parser
        self.commands[command] = func

    @micropython.viper
    def loop(self):
    
        readers, _, _ = select.select([session.stdin for session in self.sessions.values()], [], [], 0)
        
        for reader in readers:
            source_session = object()
            for session in self.sessions.values():
                if session.stdin == reader:
                    source_session = session
                    break

            line = source_session.readline()
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            line.strip()
            #if len(line) == 0: continue

            source_session.echo(line)
            
            self.execute_input(line, source_session)
    
    def execute_input(self, line_input, source_session):
        session = source_session

        words = shlex.split(line_input)
        if len(words) == 0: return # fix this

        command = words[0]
        if command is "exit":
            self.remove_session(session.name)
            return
        elif command is "cat":
            session.print(' '.join(words))

        func = self.commands[command]
        
        argss, unparsed = self.parsers[command].parse_known_args(words[1:])

        stream_out = session.stdout
        if Clivia.OPERATOR_REDIRECT_OUT in unparsed:
            if unparsed.index(Clivia.OPERATOR_REDIRECT_OUT) == len(unparsed) - 2:
                stream_out = self.sessions[unparsed[-1]].stdout
        
        try:
            kwargs = {"print": Clivia.printto(stream_out)}
            for field in dir(argss):
                if field is '__class__': continue
                kwargs[field] = getattr(argss, field)
            retval = func(**kwargs)
            #retval = func(**argss, print=lambda *a, **k: builtins.print(*a, file=stream_out, **k))
        except Exception as exc:
            sys.print_exception(exc)
            raise RuntimeError # todo other error here

    def parse_words(self, command, words):
        return self.parsers[command].parse_args(words)

    def remove_session(self, session_name):
        session = self.sessions[session_name]
        self.sessions.pop(session_name)
        session.close()
    
    @staticmethod
    def printto(sout):
        def _print(*a, **k):
            nonlocal sout
            k['file'] = sout
            return builtins.print(*a, **k)
        return _print
    
    @staticmethod
    def get_unique_session_name():
        unique_name = f'session{Clivia.SESSION_ID_COUNTER:d}'
        Clivia.SESSION_ID_COUNTER += 1
        return unique_name



class CliviaFile(CliviaSession):
    def __init__(self, input_filename, output_filename, output_mode='w', name=None):
        super().__init__(
            f"file/{Clivia.get_unique_session_name()}" if (name is None) else name,
            open(input_filename, 'r'),
            open(output_filename, output_mode))
        
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.close_in = True
        self.close_out = True

class CliviaUSB(CliviaSession):
    def __init__(self, name=None):
        super().__init__(
            f"usb/{Clivia.get_unique_session_name()}" if (name is None) else name,
            sys.stdin,
            sys.stdout)

class CliviaTCPClient(CliviaSession):
    def __init__(self, server_ip, port, blocking=False, name=None):
        self.server_ip = server_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(blocking)
        super().__init__(
            f"tcpc/{server_ip}" if (name is None) else name,
            self.socket,
            self.socket)
        self.close_in = True
    
    # Overrides: CliviaSession.open
    def open(self):
        try:
            self.socket.connect((self.server_ip, self.port))
            return super().open()
        except OSError as e:
            self.closed = True
            if e.args[0] not in [errno.EINPROGRESS, errno.ETIMEDOUT]:
                print('Error connecting', e) # todo change this
        return False

class CliviaTCPServerSession(CliviaSession):
    def __init__(self, client_ip, port, socket, name=None):
        self.client_ip = client_ip
        self.port = port
        self.socket = socket
        super().__init__(
            f"tcps/{client_ip}" if (name is None) else name,
            self.socket,
            self.socket)
        self.close_in = True
    
    '''
    # Overrides: CliviaSession.open
    def open(self):
        try:
            self.socket.connect() # reconnect
            return super().open()
        except OSError as e:
            self.closed = True
            if e.args[0] not in [errno.EINPROGRESS, errno.ETIMEDOUT]:
                print('Error connecting', e) # todo change this
        return False
    '''

class CliviaTCPServer():
    def __init__(self, ip, port, blocking=False):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        self.socket.setblocking(blocking)
        self.sessions = []
    
    def accept_clients(self, cli):
        try:
            tcp = self.socket.accept()
            if tcp is not None:
                conn, addr = tcp
                client_ip, port = addr
                session = CliviaTCPServerSession(client_ip, port, conn)
                self.sessions.append(session)
                cli.register_session(self.sessions[-1])
        except OSError as exc:
            if exc.errno == errno.EAGAIN: pass
