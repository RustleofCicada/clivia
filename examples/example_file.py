# file: example_file.py
# description: Example usage of Clivia on a file containing commands
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaFile
from examples.load_commands import load_commands

# error: stackoverflow.com/questions/4853533/select-select-with-regular-files

cli = Clivia()
load_commands(cli)

cli_file = CliviaFile('examples/input.txt', 'examples/output.txt' 'w')
cli.register_session(cli_file)

with cli:
    while not cli_file.closed:
        cli.loop()

'''
When Clivia finishes, you should see commands output in output.txt file
'''
