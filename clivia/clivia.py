import argparse
import shlex
import sys, io
import select
import socket
import builtins
from micropython import const

# specify which streams are ready for reading           (rx stream?)
# read data from one stream                             (rx stream sending)
# shlex the data                                        (rx stream > shlex)
# special commands (exit, >>)
# shlex[0] is a command, get corresponding parser       (shlex)
# send data to the parser, get args and kwargs          (shlex > parser)
# get tx stream                                         (tx stream)
# run function with args and kwargs, get return value   (parser > func)
# run return handler                                    (func > ret hand)

class CliviaSession:

    def __init__(self, stream_in_name:str, stream_out_name:str, perm_lvl:int):
        self.stream_in_name = stream_in_name
        self.stream_out_name = stream_out_name
        self.close_in = False
        self.close_out = False
        self.return_handler = CliviaSession.empty_return_handler
        self.perm_lvl = perm_lvl
        self.cache = object()
    def open(self):
        pass
    def close(self):
        pass
    #def echo(self):
    #    pass

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
        self.sessions[session.name] = session

    def add_command(self, command, func, parser: argparse.ArgumentParser, perm_lvl = 0):
        self.parsers[command] = parser
        self.commands[command] = (func, perm_lvl)

    def loop(self):
        readers, _, _ = select.select(self.in_streams.values(), [], [], self.select_timeout)
        for reader in readers:
            # rewrite this
            stream_in_name, stream = [(key, value) for key, value in self.in_streams.values() if value == reader][0]

            line = stream.readline()
            if type(line) is bytes: line = line.decode('utf-8')

            #session.echo(line)
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
            print = Clivia.print_to_stream(stream_out)

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
                raise ValueError # todo other error here

            try:
                kwargs = {"print": print}
                for field in dir(args):
                    if field is '__class__': continue # refactor this
                    kwargs[field] = getattr(args, field)
                retval = func(**kwargs)
            except Exception as exc:
                raise RuntimeError # todo other error here
            
            try:
                session.return_handler(line, retval, print=print)
            except Exception as exc:
                raise RuntimeError # todo other error here

    def close_session(self, stream_in_name):
        session = self.sessions[stream_in_name]
        self.sessions.popitem(session)
        session.close()

        if session.close_in:
            stream_in = self.in_streams[stream_in_name]
            self.in_streams.popitem(stream_in)
            stream_in.close()
            del(stream_in)
        
        if session.close_out:
            stream_out = self.out_streams[session.stream_out_name]
            self.out_streams.popitem(stream_out)
            stream_out.close()
            del(stream_out)
        
        del(session)

class CliviaStream(CliviaSession):
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

class CliviaTCPServer(CliviaSession):
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
