# file: example_file.py
# description: Example usage of Clivia on a file containing commands
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaSession
from load_commands import load_commands

cli = Clivia()
load_commands(cli)

cli_file = CliviaSession(
    open('input.txt', 'r'), 'file/input/in',
    open('output.txt', 'w'), 'file/output/out')
cli.register_session(cli_file)

with cli:
    while not cli_file.closed:
        cli.loop()

'''
When Clivia finishes, you should see commands output in output.txt file
'''
