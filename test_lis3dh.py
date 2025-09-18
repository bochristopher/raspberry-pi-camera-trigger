#!/usr/bin/env python3
"""Quick LIS3DH test script"""

import time
import board
import busio
import adafruit_lis3dh

print("Testing LIS3DH accelerometer...")

try:
    # Initialize I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x18)

    # Configure sensor
    lis3dh.range = adafruit_lis3dh.RANGE_4_G
    lis3dh.data_rate = adafruit_lis3dh.DATARATE_100_HZ

    print("LIS3DH initialized successfully!")
    print("Range:", lis3dh.range)
    print("Data rate:", lis3dh.data_rate)
    print("\nReading accelerometer data for 10 seconds...")
    print("Bump/tap the sensor to see changes!")
    print()

    for i in range(50):  # 10 seconds at 5Hz
        x, y, z = lis3dh.acceleration
        magnitude = (x*x + y*y + z*z) ** 0.5
        print(f"Sample {i+1:2d}: X={x:6.2f} Y={y:6.2f} Z={z:6.2f} Mag={magnitude:6.2f} m/s²")
        time.sleep(0.2)

    print("\nTest completed successfully!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()