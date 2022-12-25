# file: example_stream.py
# description: Example of mouning UART stream to Clivia
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaStream
from load_commands import load_commands

from machine import Pin, UART
uart = UART(0, 115200, tx=Pin(0), rx=Pin(1))

cli = Clivia()
load_commands(cli)

cli_stream = CliviaStream(uart)
cli.mount(cli_stream)

with cli:
    while True:
        cli.loop()

'''
Now try following commands on UART connection:
help
welcome -q
led 1 -v
''' 

# alternative:
with cli:
    cli.loop_forever()