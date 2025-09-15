import time, board, busio
import adafruit_lis3dh

i2c = busio.I2C(board.SCL, board.SDA)
# Try 0x18 first; use 0x19 if your board ties SA0 high
lis = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x18)

lis.range = adafruit_lis3dh.RANGE_4_G
lis.data_rate = adafruit_lis3dh.DATARATE_100_HZ

print("LIS3DH ready. Ctrl+C to stop.")
while True:
    x, y, z = lis.acceleration  # m/s^2
    print(f"{time.time():.3f}, {x:.3f}, {y:.3f}, {z:.3f}")
    time.sleep(0.02)
