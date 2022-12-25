# file: example_return_handler.py
# description: Example of handing return value from function assigned to executed command
# author: Damian Legutko (rustleofcicada@gmail.com)

import builtins
from clivia import Clivia, CliviaUSB
from load_commands import load_commands

# this function is optional
def return_handler(retval, scope, print=builtins.print):
    if retval is not None:
        print(f"Command '{scope.cmd}' returned: {retval}")
        print(f"Function details:\nfunc: {scope.func}\nargs: {scope.args}\nkwargs: {scope.kwargs}")

cli = Clivia(select_timeout = 0.5)
load_commands(cli)

cli_usb = CliviaUSB()
cli_usb.return_handler = return_handler
cli.mount(cli_usb)

with cli:
    while True:
        cli.loop() # will block for time specified in select_timeout

'''
Now try following commands:
help
welcome -q
led 1 -v
''' 

# alternative:
with cli:
    cli.loop_forever()