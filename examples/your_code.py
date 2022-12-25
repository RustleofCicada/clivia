import builtins
from machine import Pin

led = Pin("LED", Pin.OUT)

def led_control(state: bool, verbose=True, print=builtins.print) -> int:
    global led
    led.value(state)
    
    if verbose:
        print(f"Led turned {'on' if state else 'off'}.")
    
    return led.value()

def print_welcome(verbose=True, quiet=False, print=builtins.print) -> None:

    if verbose:
        print("Welcome to Clivia, CLI library via multiple interfaces on Micropython boards!")

    elif quiet:
        print("Welcome to Clivia.")
