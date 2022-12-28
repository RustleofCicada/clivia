# file: example_usb_and_tcp_server.py
# description: Example usage of interfacing with Clivia via USB and TCP simultaneously
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaUSB, CliviaTCPServer
from examples.load_commands import load_commands

from examples.your_network_code import network_connect, get_ifconfig_ip

network_connect()
ip = get_ifconfig_ip()
port = 5555

cli = Clivia()
load_commands(cli)

cli_usb = CliviaUSB()
cli.register_session(cli_usb)

tcps = CliviaTCPServer(ip, port)

with cli:
    while True:
        cli.loop()
        tcps.accept_clients(cli)
