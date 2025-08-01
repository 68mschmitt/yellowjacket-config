# YellowJacket Keyboard Configuration

A comprehensive ZMK configuration for the YellowJacket split ergonomic keyboard supporting both **QWERTY** and **Colemak** layouts with 8 specialized layers and extensive combo functionality.

> 💡 The keyboard design is based on the [Yellow Jacket keyboard by jimmerricks](https://github.com/jimmerricks/bugs), with custom modifications tailored for the Yellow Jacket layout.

## Table of Contents
- [Layout Selection](#layout-selection)
- [Physical Layout](#physical-layout)
- [Base Layers](#base-layers)
- [Home Row Mods](#home-row-mods)
- [Layers](#layers)
- [Combos](#combos)
- [Usage Guide](#usage-guide)
- [Tips and Tricks](#tips-and-tricks)
- [Getting Started](#getting-started)

## Layout Selection

This configuration includes two completely separate keymap configurations with different optimizations:

### Available Layouts:
- **QWERTY**: `yellowjacket-qwerty.keymap` - QWERTY with fast-typing optimizations
- **Colemak**: `yellowjacket-colemak.keymap` - Original Colemak configuration

### Key Differences Between Keymaps:

| Feature | QWERTY Keymap | Colemak Keymap |
|---------|---------------|----------------|
| **Base Layout** | W-E-R-T-Y-U-I-O (Q/P as combos) | W-F-P-B-J-L-U-Y (Q as combo) |
| **Thumb Layout** | BR/TAB NUM/SPACE ARR/ENTER MOUS/BSPC | NUM/SPACE BR/TAB MOUS/BSPC ARR/ENTER |
| **Home Row Timing** | 300ms tap, 175ms quick-tap | 150ms tap, 0ms quick-tap |
| **Optimization** | Fast typing & key rolling | Standard ZMK behavior |
| **Combos** | Updated for swapped thumbs | Original positions |

### Switching Layouts:

**For QWERTY:**
```bash
cp config/yellowjacket-qwerty.keymap config/yellowjacket.keymap
```

**For Colemak:**
```bash
cp config/yellowjacket-colemak.keymap config/yellowjacket.keymap
```

After copying, build your firmware as usual. The active layout is determined by the `yellowjacket.keymap` file used in the build process.

## Physical Layout

```
Key Position Reference:
╭────────────────────╮ ╭────────────────────╮
│      0   1   2   3 │ │  4   5   6   7     │
│  8   9  10  11  12 │ │ 13  14  15  16  17 │
│ 18  19  20  21  22 │ │ 23  24  25  26  27 │
╰───────────╮ 28  29 │ │ 30  31 ╭───────────╯
            ╰────────╯ ╰────────╯
```

## Base Layers

### QWERTY Layout

```
       W     E     R     T         Y     U     I     O
GUI/A  ALT/S CTRL/D SHIFT/F G     H     SHIFT/J CTRL/K ALT/L GUI/;
FN/Z   SYS/X  C     V     B       N     M     ,     .     /
             BR/TAB NUM/SPACE   ARR/ENTER MOUS/BSPC
```

### Colemak Layout

```
       W     F     P     B         J     L     U     Y
GUI/A  ALT/R CTRL/S SHIFT/T G     M     SHIFT/N CTRL/E ALT/I GUI/O
FN/Z   SYS/X  C     D     V       K     H     ,     .     /
             NUM/SPACE BR/TAB   MOUS/BSPC ARR/ENTER
```

### Key Features:
- **Dual layout support** - Choose between QWERTY familiarity or Colemak efficiency
- **Home row modifiers** for efficient modifier access
- **Layer-tap keys** on thumbs and outer columns  
- **34-key layout** optimized for split ergonomic typing
- **Identical functionality** across both layouts (layers, combos, etc.)

## Home Row Mods

The home row keys double as modifiers when held:

### QWERTY Home Row Mods:
| Key | Tap | Hold |
|-----|-----|------|
| A | A | GUI (Windows/Cmd) |
| S | S | Alt |
| D | D | Ctrl |
| F | F | Shift |
| J | J | Shift |
| K | K | Ctrl |
| L | L | Alt |
| ; | ; | GUI (Windows/Cmd) |

### Colemak Home Row Mods:
| Key | Tap | Hold |
|-----|-----|------|
| A | A | GUI (Windows/Cmd) |
| R | R | Alt |
| S | S | Ctrl |
| T | T | Shift |
| N | N | Shift |
| E | E | Ctrl |
| I | I | Alt |
| O | O | GUI (Windows/Cmd) |

**QWERTY Timing**: 300ms tapping term with 175ms quick-tap window and tap-preferred behavior. These longer timings prevent accidental modifier activation during fast typing and key rolling.

**Colemak Timing**: 150ms tapping term with 0ms quick-tap window and tap-preferred behavior. Standard ZMK timing for typical use.

## Layers

### 1. NUM Layer (Number Pad)
**Activation**: Hold `Space` key (right thumb)

```
             -     -     -     -         -     7     8     9
       -     -     -     -     -         -     4     5     6     0
       -     -     -     -     -         -     1     2     3     .
                         ■     -         -     -
```

### 2. ARR Layer (Arrows & Navigation)
**Activation**: Hold `Enter` key (right thumb)  
**Toggle**: Combo `Enter+Backspace` (thumb keys)

```
             -     -     -     -       Scrl↑  Home   ↑    PgUp
       -     -     -     -     -       Scrl↓   ←     ↓     →    GUI
       -     -     -     -     -        Ins   End   Del   PgDn  TogARR
                         -     -         -     ■
```

### 3. MOUS Layer (Mouse Control)
**Activation**: Hold `Backspace` key (right thumb)  
**Toggle**: Combo `Backspace+;` (positions 17+30)

```
            MB2   MB3   MB1  Scrl↑     Scrl↑  MB1   M↑    MB2
      -     -     -     -    Scrl↓     Scrl↓  M←    M↓    M→    -
      -     -     -     -     -        MB4   ScrlL  MB3  ScrlR  MB5
                        -     -         ■     -
```

### 4. FUNC Layer (Function Keys)
**Activation**: Hold `Z` key

```
             F9    F10   F11   F12       -     -     -     -
      ■      F5    F6    F7    F8        -     -     -     -     -
      -      F1    F2    F3    F4        -     -     -     -     -
                         -     -         -     -
```

### 5. SYS Layer (System Controls)
**Activation**: Hold `X` key

```
             -     -     -    Vol+      OUT   -     -    Studio
      -      -     -    Play  Vol-      -     BT3   BT4   BT5   BT_CLR
      -      ■     -     -    Mute      -     BT0   BT1   BT2   BT_CLR_ALL
                         -     -         -     -
```

### 6. BR Layer (Brackets)
**Activation**: Hold `Tab` key (left thumb)

```
             -     {     }     -         -     -     -     -
      -      -     (     )     -         -     -     -     -     -
      -      -     [     ]     -         -     -     -     -     -
                         -     ■         -     -
```

### 7. GA Layer (Gaming)
**Activation**: Toggle with combo `R+I` (positions 4+7)

```
             Q     W     E     1         -     -     -     -
    Shift    A     S     D     2         -     -     -     -     -
    Ctrl     -     -     -     3         -     -     -     -     -
                       Space  Tab        -     -
```

### 8. Reserved Layers
Three additional layers (extra1, extra2, extra3) are reserved for future customization.

## Combos

Combos allow you to access additional characters and functions by pressing two keys simultaneously.

**Important**: The two keymaps have different combo positions due to different thumb layouts!

### Letters & Punctuation

| Combo | QWERTY Position | QWERTY Keys | Colemak Position | Colemak Keys | Output |
|-------|-----------------|-------------|------------------|--------------|--------|
| Q | 0+1 | W+E | 9+10 | R+S | Q |
| P | 6+7 | I+O | - | - | P |
| : | 15+16 | K+L | 15+16 | E+I | : |
| ; | 24+25 | M+, | 24+25 | H+, | ; |
| Esc | 10+11 OR 14+15 | D+F OR J+K | 10+11 OR 14+15 | S+T OR N+E | Esc |

**Note**: QWERTY has both Q and P as combos. Colemak only has Q as combo (P is direct on base layer).

### Quick Numbers

| Number | QWERTY (Enter+Key) | QWERTY Position | Colemak (Enter+Key) | Colemak Position |
|--------|-------------------|-----------------|-------------------|------------------|
| 0 | Enter+; | 30+17 | Enter+O | 31+17 |
| 1 | Enter+M | 30+24 | Enter+M | 31+24 |
| 2 | Enter+, | 30+25 | Enter+, | 31+25 |
| 3 | Enter+. | 30+26 | Enter+. | 31+26 |
| 4 | Enter+J | 30+14 | Enter+N | 31+14 |
| 5 | Enter+K | 30+15 | Enter+E | 31+15 |
| 6 | Enter+L | 30+16 | Enter+I | 31+16 |
| 7 | Enter+Y | 30+5 | Enter+L | 31+5 |
| 8 | Enter+U | 30+6 | Enter+U | 31+6 |
| 9 | Enter+I | 30+7 | Enter+Y | 31+7 |

### Special Characters

| Character | QWERTY (Bspc+Key) | QWERTY Position | Colemak (Bspc+Key) | Colemak Position |
|-----------|-------------------|-----------------|-------------------|------------------|
| ! | Bspc+M | 31+24 | Bspc+M | 30+24 |
| @ | Bspc+, | 31+25 | Bspc+, | 30+25 |
| # | Bspc+. | 31+26 | Bspc+. | 30+26 |
| $ | Bspc+J | 31+14 | Bspc+N | 30+14 |
| % | Bspc+K | 31+15 | Bspc+E | 30+15 |
| ^ | Bspc+L | 31+16 | Bspc+I | 30+16 |
| & | Bspc+Y | 31+5 | Bspc+L | 30+5 |
| * | Bspc+U | 31+6 | Bspc+U | 30+6 |
| ( | Bspc+I | 31+7 | Bspc+Y | 30+7 |

### Quotes

| Character | QWERTY (Space+Key) | QWERTY Position | Colemak (Space+Key) | Colemak Position |
|-----------|-------------------|-----------------|-------------------|------------------|
| ~ | Space+Z | 29+18 | Space+Z | 28+18 |
| ` | Space+S | 29+9 | Space+R | 28+9 |
| ' | Space+D | 29+10 | Space+S | 28+10 |
| " | Space+F | 29+11 | Space+T | 28+11 |

### Operators & Symbols

| Symbol | QWERTY Combo | QWERTY Position | Colemak Combo | Colemak Position | Description |
|--------|--------------|-----------------|---------------|------------------|-------------|
| = | N+Bspc | 23+31 | M+Bspc | 23+30 | Equals |
| + | T+Bspc | 4+31 | J+Bspc | 4+30 | Plus |
| - | H+Bspc | 13+31 | M+Bspc | 13+30 | Minus |
| _ | X+C | 19+20 | X+C | 19+20 | Underscore |
| \ | Bspc+/ | 31+27 | Bspc+/ | 30+27 | Backslash |
| \| | /+Enter | 27+30 | /+Enter | 27+31 | Pipe |

### Layer Toggles

| Function | QWERTY Combo | QWERTY Position | Colemak Combo | Colemak Position |
|----------|--------------|-----------------|---------------|------------------|
| Mouse Toggle | ;+Bspc | 17+31 | O+Bspc | 17+30 |
| Arrow Toggle | Bspc+Enter | 31+30 | Bspc+Enter | 30+31 |
| Gaming Toggle | R+I | 4+7 | B+Y | 4+7 |

### Special Functions

| Combo | Keys | Function |
|-------|------|----------|
| Turbo Shift | Both thumb keys | Shift (emergency shift) |

## Usage Guide

### Basic Typing
1. **Normal typing**: Use like any QWERTY keyboard
2. **Modifiers**: Hold home row keys for 300ms+ for Ctrl, Alt, Shift, GUI
3. **Numbers**: Hold Space (right thumb) + right hand for number pad
4. **Arrows**: Hold Enter (right thumb) for navigation

### Layer Access Patterns
- **Temporary**: Hold layer key → type → release
- **Toggle**: Use combo to lock layer → type → toggle again to unlock
- **One-shot**: Tap layer key for single character access (where supported)

### Efficient Workflows

#### Programming
1. **Brackets**: Hold Tab (left thumb) for (), [], {}
2. **Numbers**: Hold Space (right thumb) for number pad
3. **Special chars**: Use Backspace combos for !@#$%^&*
4. **Navigation**: Hold Enter (right thumb) for arrows and page keys

#### Gaming
1. **Toggle gaming layer**: R+I combo
2. **Standard WASD** with left shift and ctrl
3. **Quick numbers** 1-3 on right side
4. **Toggle back**: R+I combo again

#### System Control
1. **Bluetooth**: Hold X → BT0-5 for pairing, BT_CLR to disconnect
2. **Media**: Hold X → Play/Pause, Volume controls
3. **Mouse**: Hold Backspace (right thumb) or toggle with ;+Backspace combo

## Tips and Tricks

### Home Row Mods
- **Practice slowly** - let muscle memory develop for the 300ms timing
- **Tap quickly** for letters (under 175ms), **hold deliberately** for modifiers (300ms+)
- **Key rolling friendly** - longer timings prevent accidental modifier activation
- **Use opposite hand** for modifier+key combinations when possible

### Combo Mastery
- **Thumb combos** are easiest - start with Space+letter for quotes
- **Practice number combos** with Enter+right hand keys
- **Emergency shift** (both thumbs) when home row mods fail

### Layer Efficiency
- **Learn one layer at a time** - start with NUM layer
- **Use toggles** for extended work in arrow/mouse layers
- **Gaming layer** completely changes left side - practice mode switching

### Troubleshooting
- **Stuck in layer?** Use the same toggle combo to exit
- **Modifier stuck?** Tap the home row key to release
- **Bluetooth issues?** Use BT_CLR_ALL in SYS layer

### Customization
- Modify `yellowjacket.keymap` for personal preferences
- Adjust `tapping-term-ms` (currently 300ms) and `quick-tap-ms` (currently 175ms) in behaviors section for home row mod timing
- Add custom combos using the COMBO macro pattern

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/68mschmitt/yellowjacket-config.git
cd yellowjacket-config
```

### 2. Set Up the Environment

Follow the [ZMK development setup guide](https://zmk.dev/docs/development/setup) to install prerequisites and prepare your build environment.

### 3. Build the Firmware

Use `west` or your preferred build tool to compile the firmware. You can also reference `build.yaml` for common configurations.

### 4. Flash to Your Keyboard

Once built, flash the `.uf2` or `.hex` files to your Yellow Jacket keyboard using the appropriate method for your microcontroller (e.g., drag-and-drop UF2 flashing or DFU).

---

## Repository Structure

- `boards/shields/` - Custom shield definitions for the Yellow Jacket keyboard
- `config/` - Contains keymap configuration, layer definitions, and user preferences  
- `zephyr/` - Includes Zephyr RTOS configuration files used by ZMK
- `.github/workflows/` - GitHub Actions CI workflows for building and testing firmware
- `build.yaml` - Configuration file used for building the firmware with ZMK's west build system

---

## Contributing

Issues and pull requests are welcome. Feel free to suggest layout tweaks, firmware enhancements, or documentation improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

*For technical details, see the `yellowjacket.keymap` configuration file.*

