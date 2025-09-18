#!/usr/bin/env python3
"""Manual trigger test - simulate GPIO interrupt"""

import time
from gpiozero import Button

print("Testing GPIO17 interrupt simulation...")
print("This will manually trigger the camera system...")

# Simulate the interrupt that would come from LIS3DH
button = Button(17, pull_up=True)

def trigger_callback():
    print("*** GPIO17 INTERRUPT TRIGGERED ***")
    print("This simulates what the LIS3DH should do when tapped")

button.when_pressed = trigger_callback

print("Simulating LIS3DH tap in 3 seconds...")
print("You should see trigger events in the main application...")

time.sleep(3)

# Force trigger by briefly connecting GPIO17 to ground
print("TRIGGERING NOW!")
button._pin.gpio.output(17, 0)  # Pull low briefly
time.sleep(0.1)
button._pin.gpio.output(17, 1)  # Release

print("Trigger simulation complete!")
time.sleep(2)