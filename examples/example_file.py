# file: example_file.py
# description: Example usage of Clivia on a file containing commands
# author: Damian Legutko (rustleofcicada@gmail.com)

from clivia import Clivia, CliviaFile
from load_commands import load_commands

cli = Clivia()
load_commands(cli)

cli_file = CliviaFile(
    input='input.txt',
    output='output.txt',
    output_mode='a')
cli.mount(cli_file)

with cli:
    while not cli_file.completed():
        cli.loop()

'''
When Clivia finishes, you should see commands output in output.txt file
'''
