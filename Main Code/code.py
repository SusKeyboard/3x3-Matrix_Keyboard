# ╔══════════════════════════════════════════════════════════════════╗
# ║         OceanLabz RP2040 — 3×3 Macropad Firmware               ║
# ║         CircuitPython 9.x · USB HID · SSD1306 OLED             ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║  Pin mapping — sourced directly from pcbwiring.pdf (KiCad)      ║
# ║                                                                  ║
# ║  OLED J1  (SSD1306 128×32)                                      ║
# ║    SDA  → GP28   (RP2040-Zero left pad "29")                    ║
# ║    SCL  → GP29   (RP2040-Zero left pad "28")                    ║
# ║    VCC  → 3V3                                                    ║
# ║    GND  → GND                                                    ║
# ║                                                                  ║
# ║  Key Matrix  (3 rows × 3 cols, diodes on rows)                  ║
# ║    Row 0 → GP1    Row 1 → GP2    Row 2 → GP3                   ║
# ║    Col 0 → GP4    Col 1 → GP5    Col 2 → GP6                   ║
# ║                                                                  ║
# ║  Encoder MT1  (PEC11R-4215F-S0024)                              ║
# ║    A (CLK) → GP7                                                 ║
# ║    B (DT)  → GP8                                                 ║
# ║    SW      → GP9   (push-button S2, active-low)                 ║
# ║    COM     → GND                                                 ║
# ║    +/Shield→ 3V3 / GND                                          ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║  Required libraries — copy to CIRCUITPY/lib/                    ║
# ║    circup install adafruit_hid adafruit_ssd1306                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import board
import busio
import digitalio
import time
import usb_hid

from adafruit_hid.keyboard              import Keyboard
from adafruit_hid.keyboard_layout_us   import KeyboardLayoutUS
from adafruit_hid.keycode               import Keycode
from adafruit_hid.consumer_control      import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import adafruit_ssd1306

# ──────────────────────────────────────────────────────────────────
#  TIMING HELPERS  (CircuitPython has no ticks_ms / ticks_diff)
# ──────────────────────────────────────────────────────────────────

def ticks_ms():
    return time.monotonic_ns() // 1_000_000

def ticks_diff(newer, older):
    return newer - older

# ──────────────────────────────────────────────────────────────────
#  PIN CONFIGURATION  — from pcbwiring.pdf schematic
# ──────────────────────────────────────────────────────────────────

OLED_W = 128
OLED_H = 32

# Key matrix
ROW_BOARD_PINS = [board.GP1, board.GP2, board.GP3]   # Row 0, 1, 2
COL_BOARD_PINS = [board.GP4, board.GP5, board.GP6]   # Col 0, 1, 2

# Encoder PEC11R-4215F-S0024
ENC_CLK_PIN = board.GP7    # A
ENC_DT_PIN  = board.GP8    # B
ENC_SW_PIN  = board.GP9    # push-button S2

DEBOUNCE_MS  = 20   # key / button debounce window (ms)
ENC_DEBOUNCE = 3    # encoder pulse settle time (ms)

# ──────────────────────────────────────────────────────────────────
#  MODE DEFINITIONS
# ──────────────────────────────────────────────────────────────────

MODES = ["Blender", "Apple Music", "Photoshop"]

# Sentinel — key does nothing
NOOP = ("NOOP",)

# ── Blender ───────────────────────────────────────────────────────
#  SW1 Grab       SW2 Rotate     SW3 Scale
#  SW4 Extrude    SW5 Loop Cut   SW6 Fill
#  SW7 Render     SW8 Undo       SW9 Redo
BLENDER_KEYS = [
    ((),                               Keycode.G),          # Grab
    ((),                               Keycode.R),          # Rotate
    ((),                               Keycode.S),          # Scale
    ((),                               Keycode.E),          # Extrude
    ((Keycode.CONTROL,),               Keycode.R),          # Loop Cut
    ((),                               Keycode.F),          # Fill
    ((Keycode.F12,),                   None),               # Render (F12)
    ((Keycode.CONTROL,),               Keycode.Z),          # Undo
    ((Keycode.CONTROL, Keycode.SHIFT), Keycode.Z),          # Redo
]

# ── Apple Music ───────────────────────────────────────────────────
#  SW1 Prev       SW2 Play/Pause  SW3 Next
#  SW4 Shuffle*   SW5 Repeat*     SW6 —
#  SW7 Mute       SW8 —           SW9 —
#  Encoder always controls system volume regardless of mode
MUSIC_KEYS = [
    ("CONSUMER", ConsumerControlCode.SCAN_PREVIOUS_TRACK),
    ("CONSUMER", ConsumerControlCode.PLAY_PAUSE),
    ("CONSUMER", ConsumerControlCode.SCAN_NEXT_TRACK),
    ((Keycode.CONTROL, Keycode.ALT), Keycode.S),   # Shuffle shortcut
    ((Keycode.CONTROL, Keycode.ALT), Keycode.R),   # Repeat shortcut
    NOOP,
    ("CONSUMER", ConsumerControlCode.MUTE),
    NOOP,
    NOOP,
]

# ── Photoshop ─────────────────────────────────────────────────────
#  SW1 Brush      SW2 Eraser      SW3 Lasso
#  SW4 Fill       SW5 Clone Stamp SW6 Levels
#  SW7 Undo       SW8 Redo        SW9 Save
PHOTOSHOP_KEYS = [
    ((),                               Keycode.B),          # Brush
    ((),                               Keycode.E),          # Eraser
    ((),                               Keycode.L),          # Lasso
    ((Keycode.ALT,),                   Keycode.BACKSPACE),  # Fill (Alt+Del)
    ((),                               Keycode.S),          # Clone Stamp
    ((Keycode.CONTROL,),               Keycode.L),          # Levels
    ((Keycode.CONTROL,),               Keycode.Z),          # Undo
    ((Keycode.CONTROL, Keycode.SHIFT), Keycode.Z),          # Redo
    ((Keycode.CONTROL,),               Keycode.S),          # Save
]

MODE_KEYMAPS = [BLENDER_KEYS, MUSIC_KEYS, PHOTOSHOP_KEYS]

MODE_HINTS = [
    "G R S E F|Render",
    "<< >|> >> | Knob",
    "B E L Lvls|Save",
]

# ──────────────────────────────────────────────────────────────────
#  HARDWARE INIT
# ──────────────────────────────────────────────────────────────────

# USB HID
kbd = Keyboard(usb_hid.devices)
_   = KeyboardLayoutUS(kbd)
cc  = ConsumerControl(usb_hid.devices)

# I2C — GP28=SDA, GP29=SCL  (from schematic left-side pads 29/28)
i2c  = busio.I2C(scl=board.GP29, sda=board.GP28, frequency=400_000)
oled = adafruit_ssd1306.SSD1306_I2C(OLED_W, OLED_H, i2c)

# Key matrix rows — OUTPUT, driven HIGH one at a time during scan
rows = []
for pin in ROW_BOARD_PINS:
    p = digitalio.DigitalInOut(pin)
    p.direction = digitalio.Direction.OUTPUT
    p.value = False
    rows.append(p)

# Key matrix cols — INPUT with PULL_DOWN; reads HIGH when row is driven
cols = []
for pin in COL_BOARD_PINS:
    p = digitalio.DigitalInOut(pin)
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.DOWN
    cols.append(p)

# Encoder — all INPUT with PULL_UP (COM tied to GND = active-low signals)
enc_clk = digitalio.DigitalInOut(ENC_CLK_PIN)
enc_clk.direction = digitalio.Direction.INPUT
enc_clk.pull = digitalio.Pull.UP

enc_dt = digitalio.DigitalInOut(ENC_DT_PIN)
enc_dt.direction = digitalio.Direction.INPUT
enc_dt.pull = digitalio.Pull.UP

enc_sw = digitalio.DigitalInOut(ENC_SW_PIN)
enc_sw.direction = digitalio.Direction.INPUT
enc_sw.pull = digitalio.Pull.UP

# ──────────────────────────────────────────────────────────────────
#  STATE
# ──────────────────────────────────────────────────────────────────

current_mode = 0
key_pressed  = [False] * 9
key_last_t   = [0]     * 9

enc_clk_last = enc_clk.value
enc_sw_last  = enc_sw.value
enc_sw_t     = 0

# ──────────────────────────────────────────────────────────────────
#  OLED RENDERING
# ──────────────────────────────────────────────────────────────────

def draw_screen(mode_idx):
    """
    128×32 layout:
      y 0–10  : three mode indicator squares (filled = active)
      y 12–19 : mode name  (built-in 8×8 font)
      y 22–29 : shortcut hint line
    """
    oled.fill(0)

    # Mode indicator squares
    sq_x = 4
    for i in range(len(MODES)):
        if i == mode_idx:
            oled.fill_rect(sq_x, 1, 9, 9, 1)   # filled = active
        else:
            oled.rect(sq_x, 1, 9, 9, 1)         # outline = inactive
        sq_x += 16

    labels = ["BLENDER", "MUSIC", "PHOTOSHOP"]
    oled.text(labels[mode_idx], 0, 13, 1)
    oled.text(MODE_HINTS[mode_idx][:21], 0, 23, 1)
    oled.show()


def splash():
    oled.fill(0)
    oled.text("  MACROPAD v2.0", 0, 4,  1)
    oled.text("OceanLabz RP2040", 0, 13, 1)
    oled.text(" 3x3 + Encoder ", 0, 22, 1)
    oled.show()
    time.sleep(1.8)
    oled.fill(0)
    oled.show()

# ──────────────────────────────────────────────────────────────────
#  KEY ACTION DISPATCH
# ──────────────────────────────────────────────────────────────────

def send_key(action):
    """
    NOOP              → nothing
    ("CONSUMER", cc)  → ConsumerControl.send(cc)
    (mods, keycode)   → press mods + key, release_all
    ((F12,), None)    → press the single keycode stored in mods tuple
    """
    if action is NOOP or (isinstance(action, tuple) and action[0] == "NOOP"):
        return

    if isinstance(action, tuple) and action[0] == "CONSUMER":
        cc.send(action[1])
        return

    mods, key = action

    if key is None:           # e.g. F12 stored in mods[0]
        if mods:
            kbd.press(mods[0])
            time.sleep(0.03)
            kbd.release_all()
        return

    if mods:
        kbd.press(*mods)
    kbd.press(key)
    time.sleep(0.03)
    kbd.release_all()

# ──────────────────────────────────────────────────────────────────
#  KEY MATRIX SCAN
# ──────────────────────────────────────────────────────────────────

def scan_matrix():
    """
    Strobes each row HIGH; reads columns.
    Returns indices (0–8) of keys that just transitioned released → pressed.
    Note: .value is a property in CircuitPython, not a method call.
    """
    now = ticks_ms()
    newly_pressed = []

    for r_idx, row in enumerate(rows):
        row.value = True
        for c_idx, col in enumerate(cols):
            k   = r_idx * 3 + c_idx
            raw = col.value             # True = switch closed

            if raw and not key_pressed[k]:
                if ticks_diff(now, key_last_t[k]) >= DEBOUNCE_MS:
                    key_pressed[k] = True
                    key_last_t[k]  = now
                    newly_pressed.append(k)

            elif not raw and key_pressed[k]:
                key_pressed[k] = False

        row.value = False

    return newly_pressed

# ──────────────────────────────────────────────────────────────────
#  ROTARY ENCODER
# ──────────────────────────────────────────────────────────────────

def read_encoder():
    """
    Quadrature decode on A (CLK) / B (DT).
    COM is wired to GND so both lines idle HIGH; pulses go LOW.
    Returns +1 (CW = vol up), -1 (CCW = vol down), 0 (no change).
    """
    global enc_clk_last
    clk = enc_clk.value
    direction = 0

    if clk != enc_clk_last:
        t0 = ticks_ms()
        while ticks_diff(ticks_ms(), t0) < ENC_DEBOUNCE:
            pass                        # settle wait
        clk = enc_clk.value
        if clk != enc_clk_last:
            dt = enc_dt.value
            direction    = 1 if (dt != clk) else -1
            enc_clk_last = clk

    return direction


def read_encoder_button():
    """
    Detects a clean encoder-button release (active-low, pull-up).
    Returns True exactly once per click.
    """
    global enc_sw_last, enc_sw_t
    now = ticks_ms()
    sw  = enc_sw.value             # True = released, False = pressed

    if not sw and enc_sw_last:
        enc_sw_t    = now          # falling edge — record press time
        enc_sw_last = sw

    elif sw and not enc_sw_last:
        if ticks_diff(now, enc_sw_t) >= DEBOUNCE_MS:
            enc_sw_last = sw
            return True            # rising edge after valid hold

    enc_sw_last = sw
    return False

# ──────────────────────────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────────────────────────

def main():
    global current_mode

    splash()
    draw_screen(current_mode)

    while True:
        # Encoder button → advance mode
        if read_encoder_button():
            current_mode = (current_mode + 1) % len(MODES)
            draw_screen(current_mode)
            time.sleep(0.05)        # brief lock-out to avoid double-fire

        # Encoder rotation → volume (works in every mode)
        delta = read_encoder()
        if delta == 1:
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
        elif delta == -1:
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)

        # Key matrix → mode hotkeys
        for k in scan_matrix():
            send_key(MODE_KEYMAPS[current_mode][k])

        time.sleep(0.0005)          # ~2 kHz poll rate


main()
