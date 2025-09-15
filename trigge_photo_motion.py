import time, math, subprocess, board, busio
import adafruit_lis3dh

i2c = busio.I2C(board.SCL, board.SDA)
lis = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x18)
lis.range = adafruit_lis3dh.RANGE_4_G
lis.data_rate = adafruit_lis3dh.DATARATE_100_HZ

GRAV = 9.81
DELTA = 1.0     # m/s^2 over/under gravity to trigger (tune this)
COOLDOWN = 2.0  # seconds between captures

last = 0
print("Ready: Move the board to trigger a photo. Ctrl+C to exit.")
while True:
    x, y, z = lis.acceleration
    mag = math.sqrt(x*x + y*y + z*z)
    if abs(mag - GRAV) > DELTA and (time.time() - last) > COOLDOWN:
        ts = int(time.time())
        out = f"capture_{ts}.jpg"
        print(f"Motion! |a|={mag:.2f} → {out}")
        subprocess.run(["fswebcam", "-r", "1280x720", "--no-banner", out], check=False)
        last = time.time()
    time.sleep(0.01)
