# 🖥️ RP2040 3x3 Macropad with Encoder - Multi Mode (HID)

This project is a **3x3 matrix-based macropad** built using an RP2040 board (like Ocean Labz RP2040-Zero) with a **rotary encoder** for **mode switching and volume control**. It supports **three modes**:

1. 🎹 Matrix Hotkeys (9 programmable keys)
2. 🔊 Volume Control (via encoder)
3. 🎯 Custom/Future Mode (e.g. mute toggle)

---

## 📦 Features

- 9-key matrix input (3x3 layout)
- Rotary encoder for:
  - Volume up/down
  - Mode switching (via encoder button)
- Supports 3 customizable modes
- HID keyboard support using CircuitPython

---

## 🛠️ Hardware Pin Mapping

### 🔢 Matrix Keypad

| Function  | GPIO Pins      |
|----------|----------------|
| Rows     | GP2, GP3, GP4   |
| Columns  | GP5, GP6, GP7   |

### 🔄 Rotary Encoder

| Encoder Part    | GPIO Pin |
|----------------|----------|
| CLK (A)        | GP8      |
| DT (B)         | GP9      |
| Button (SW)    | GP10     |

---

## 🔧 Customization Guide

### 🎹 1. Change Matrix Key Mapping

Edit the `keys` list to match your preferred keycodes (e.g., letters, shortcuts, media controls):

```python
keys = [
    [Keycode.F13, Keycode.F14, Keycode.F15],
    [Keycode.F16, Keycode.F17, Keycode.F18],
    [Keycode.F19, Keycode.F20, Keycode.F21]
]











##################################################################################   Made By :- Nityanta Kuzhikat    ##########################################################################################
