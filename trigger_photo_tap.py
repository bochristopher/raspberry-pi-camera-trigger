import time, subprocess, board, busio
import adafruit_lis3dh
from gpiozero import Button

# --- Sensor setup
i2c = busio.I2C(board.SCL, board.SDA)
lis = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x18)
lis.range = adafruit_lis3dh.RANGE_4_G
lis.data_rate = adafruit_lis3dh.DATARATE_100_HZ

# Enable single-tap on INT1 (tune threshold: 0–127; higher = harder tap)
# time_limit/latency/window are in 1/ODR units; defaults are OK as a start.
try:
    lis.set_tap(adafruit_lis3dh.TAP_SINGLE, threshold=60, time_limit=10, time_latency=20, time_window=255)
except AttributeError:
    # Older library fallback: just poll acceleration (see Option A - Motion below)
    print("set_tap not available in this driver version; use motion threshold mode.")
    raise SystemExit(1)

# --- GPIO interrupt pin (INT1 -> GPIO17)
tap = Button(17, pull_up=True)  # LIS3DH INT pins are active-low by default

def snap_photo():
    ts = int(time.time())
    out = f"capture_{ts}.jpg"
    # Change resolution if you like
    cmd = ["fswebcam", "-r", "1280x720", "--no-banner", out]
    print("Tap detected → taking photo:", out)
    subprocess.run(cmd, check=False)

print("Ready: Tap the sensor to snap a photo. Ctrl+C to exit.")
while True:
    tap.wait_for_press()   # waits for INT1 to assert
    snap_photo()
    time.sleep(0.3)        # simple debounce
