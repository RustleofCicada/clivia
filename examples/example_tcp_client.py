# file: example_file.py
# description: Example usage for interfacing with Clivia from TCP server
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaTCPClient
from load_commands import load_commands

from your_network_code import network_connect

network_connect()
server_ip = '192.168.0.2' # write your TCP server ip here!!!
port = 5555

cli = Clivia()
load_commands(cli)

cli_tcpc = CliviaTCPClient(server_ip, port)
cli.register_session(cli_tcpc)

with cli:
    while True:
        cli.loop()

'''
Try following commands on TCP server:
help
welcome -q
led 1 -v
'''

# alternative:
with cli:
    cli.loop_forever()