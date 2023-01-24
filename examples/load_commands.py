from argparse import ArgumentParser as ap
from examples import your_code

def load_commands(cli):

    p = ap(prog='led', description='Controls an led')
    p.add_argument('state', type=bool, help='Led state: 0 or 1')
    p.add_argument("-v", "--verbose", dest="verbose", action="store_const", const=True, default=False)
    cli.add_command('led', your_code.led_control, p)

    p = ap(prog='welcome', description='Prints welcome message')
    p.func = your_code.print_welcome
    p.add_argument("-v", "--verbose", dest="verbose", action="store_const", const=True, default=True)
    p.add_argument("-q", "--quiet",   dest="quiet",   action="store_const", const=True, default=False)
    cli.add_command('welcome', your_code.print_welcome, p)

