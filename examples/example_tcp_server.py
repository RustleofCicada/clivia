# file: example_file.py
# description: Example usage for interfacing with Clivia from TCP client
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaTCPServer
from load_commands import load_commands

from your_network_code import network_connect, get_ifconfig_ip

network_connect()
ip = get_ifconfig_ip()
port = 5555

def on_client_connected(client_ip, client_port):
    print(f"New TCP client connected to Clivia: {client_ip}, {client_port}")

cli = Clivia()
load_commands(cli)

cli_tcps = CliviaTCPServer(ip, port)
cli_tcps.on_new_client = on_client_connected
cli.mount(cli_tcps)

print(f"Clivia TCP server starting on IP: {ip}")

with cli:
    while True:
        cli.loop()
        cli_tcps.accept_clients()

'''
Connect via TCP connection and try following commands:
help
welcome -q
led 1 -v
'''

# alternative:
with cli:
    cli.loop_forever()