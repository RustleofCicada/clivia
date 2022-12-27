# file: example_file.py
# description: Example usage of mounting USB connection to Clivia
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaUSB
from examples.load_commands import load_commands

cli = Clivia()
load_commands(cli)

cli_usb = CliviaUSB()
cli.register_session(cli_usb)

with cli:
    while True:
        cli.loop()

'''
Now try following commands on USB connection:
help
welcome -q
led 1 -v
''' 

# alternative:
with cli:
    cli.loop_forever()
