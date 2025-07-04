import time
import board # type: ignore
import digitalio # type: ignore
import usb_hid # type: ignore
from adafruit_hid.keyboard import Keyboard # type: ignore
from adafruit_hid.keycode import Keycode # type: ignore
from adafruit_matrixkeypad import Matrix_Keypad # type: ignore
from digitalio import DigitalInOut, Direction, Pull # type: ignore
# === Encoder Pins ===
encoder_clk = digitalio.DigitalInOut(board.GP8)
encoder_clk.direction = digitalio.Direction.INPUT
encoder_clk.pull = digitalio.Pull.UP
encoder_dt = digitalio.DigitalInOut(board.GP9)
encoder_dt.direction = digitalio.Direction.INPUT
encoder_dt.pull = digitalio.Pull.UP
encoder_btn = digitalio.DigitalInOut(board.GP10)
encoder_btn.direction = digitalio.Direction.INPUT
encoder_btn.pull = digitalio.Pull.UP
# === Matrix Setup ===
cols = [DigitalInOut(x) for x in (board.GP5, board.GP6, board.GP7)]
rows = [DigitalInOut(x) for x in (board.GP2, board.GP3, board.GP4)]

keys = [
    [Keycode.F13, Keycode.F14, Keycode.F15],
    [Keycode.F16, Keycode.F17, Keycode.F18],
    [Keycode.F19, Keycode.F20, Keycode.F21]
]

keypad = Matrix_Keypad(rows, cols, keys)
kbd = Keyboard(usb_hid.devices)
# === State Tracking ===
mode = 1
last_btn_state = encoder_btn.value
last_clk = encoder_clk.value
last_mode_print = -1
print("MacroPad Ready")
while True:
# Mode switching with encoder button
    if not encoder_btn.value and last_btn_state:
        mode += 1
        if mode > 3:
            mode = 1
        print("Switched to Mode", mode)
        time.sleep(0.3) # Debounce
last_btn_state = encoder_btn.value
# Show mode once
if mode != last_mode_print: 
    print(f"--- Mode {mode} Active ---")
    last_mode_print = mode
# === Mode 1: Matrix Keys ===
if mode == 1:
    pressed = keypad.pressed_keys
    for key in pressed:
        kbd.press(key)
    if not pressed:
        kbd.release_all()
# === Mode 2: Volume Control ===
elif mode == 2:
    clk_state = encoder_clk.value
    dt_state = encoder_dt.value
    if clk_state != last_clk:
        if dt_state != clk_state:
            print("Volume Up")
            kbd.send(Keycode.VOLUME_INCREMENT)
        else:
            print("Volume Down")
            kbd.send(Keycode.VOLUME_DECREMENT)
        time.sleep(0.1) # Prevent rapid repeat
    last_clk = clk_state
# === Mode 3: Future Mode ===
elif mode == 3:
# Example: mute toggle on encoder rotation
    clk_state = encoder_clk.value
    dt_state = encoder_dt.value
    if clk_state != last_clk:
        print("Mute Toggle")
        kbd.send(Keycode.MUTE)
        time.sleep(0.2)
    last_clk = clk_state
    
time.sleep(0.01)

