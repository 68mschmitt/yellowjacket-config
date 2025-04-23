# Yellow Jacket ZMK Configuration

This repository contains the ZMK firmware configuration for the **Yellow Jacket** mechanical keyboard, which is internally referred to as **gnat** in the code.

> 💡 The keyboard design is based on the [gnat keyboard by jonkeykong](https://github.com/jonkeykong/gnat), with custom modifications tailored for the Yellow Jacket layout.

---

## 🗂 Repository Structure

- `boards/shields/`  
  Custom shield definitions for the Yellow Jacket keyboard.

- `config/`  
  Contains keymap configuration, layer definitions, and user preferences.

- `zephyr/`  
  Includes Zephyr RTOS configuration files used by ZMK.

- `.github/workflows/`  
  GitHub Actions CI workflows for building and testing firmware.

- `build.yaml`  
  Configuration file used for building the firmware with ZMK's west build system.

---

## 🚀 Getting Started

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

Once built, flash the `.uf2` or `.hex` files to your Yellow Jacket keyboard (gnat) using the appropriate method for your microcontroller (e.g., drag-and-drop UF2 flashing or DFU).

---

## 📝 Notes

- The keyboard is referred to as `gnat` internally within the configuration and file structure.
- This repo is optimized for use with ZMK on nRF-based microcontrollers (like nice!nano v2).
- Ensure all dependencies are installed correctly for ZMK and Zephyr development.

---

## 🤝 Contributing

Issues and pull requests are welcome. Feel free to suggest layout tweaks, firmware enhancements, or documentation improvements.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

