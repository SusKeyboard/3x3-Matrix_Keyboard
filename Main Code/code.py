import time
import board # type: ignore
import digitalio # type: ignore
import usb_hid # type: ignore
from adafruit_hid.keyboard import Keyboard # type: ignore
from adafruit_hid.keycode import Keycode # type: ignore
from adafruit_matrixkeypad import Matrix_Keypad # type: ignore
from adafruit_debouncer import Debouncer # type: ignore

# ========== Encoder Setup ==========
encoder_clk_pin = digitalio.DigitalInOut(board.GP8)
encoder_clk_pin.direction = digitalio.Direction.INPUT
encoder_clk_pin.pull = digitalio.Pull.UP

encoder_dt_pin = digitalio.DigitalInOut(board.GP9)
encoder_dt_pin.direction = digitalio.Direction.INPUT
encoder_dt_pin.pull = digitalio.Pull.UP

encoder_btn_raw = digitalio.DigitalInOut(board.GP10)
encoder_btn_raw.direction = digitalio.Direction.INPUT
encoder_btn_raw.pull = digitalio.Pull.UP
encoder_btn = Debouncer(encoder_btn_raw)

# ========== Matrix Keypad Setup ==========
cols = [digitalio.DigitalInOut(x) for x in (board.GP5, board.GP6, board.GP7)]
rows = [digitalio.DigitalInOut(x) for x in (board.GP2, board.GP3, board.GP4)]

for pin in cols + rows:
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP

keymap = [
    [Keycode.F13, Keycode.F14, Keycode.F15],
    [Keycode.F16, Keycode.F17, Keycode.F18],
    [Keycode.F19, Keycode.F20, Keycode.F21]
]

keypad = Matrix_Keypad(rows, cols, keymap)
kbd = Keyboard(usb_hid.devices)

# ========== State ==========
mode = 1
last_clk = encoder_clk_pin.value
last_pressed_keys = set()
NUM_MODES = 3

print("🎉 Macropad Ready!")

def switch_mode():
    global mode
    mode += 1
    if mode > NUM_MODES:
        mode = 1
    print(f"🔁 Switched to Mode {mode}")

def handle_mode_1():
    global last_pressed_keys
    current_keys = set(keypad.pressed_keys)

    # Release keys that are no longer pressed
    for key in last_pressed_keys - current_keys:
        kbd.release(key)

    # Press newly pressed keys
    for key in current_keys - last_pressed_keys:
        kbd.press(key)

    last_pressed_keys = current_keys

def handle_mode_2():
    global last_clk
    clk_state = encoder_clk_pin.value
    dt_state = encoder_dt_pin.value

    if clk_state != last_clk:
        if dt_state != clk_state:
            print("🔊 Volume Up")
            kbd.send(Keycode.VOLUME_INCREMENT)
        else:
            print("🔉 Volume Down")
            kbd.send(Keycode.VOLUME_DECREMENT)
        time.sleep(0.05)  # Optional short delay
    last_clk = clk_state

def handle_mode_3():
    global last_clk
    clk_state = encoder_clk_pin.value
    if clk_state != last_clk:
        print("🔇 Mute Toggled")
        kbd.send(Keycode.MUTE)
        time.sleep(0.1)
    last_clk = clk_state

# ========== Main Loop ==========
while True:
    encoder_btn.update()

    # Handle mode switching
    if encoder_btn.fell:
        switch_mode()
        time.sleep(0.05)  # Minor debounce

    # Handle per-mode behavior
    if mode == 1:
        handle_mode_1()
    elif mode == 2:
        handle_mode_2()
    elif mode == 3:
        handle_mode_3()

    time.sleep(0.01)  # Short idle delay
