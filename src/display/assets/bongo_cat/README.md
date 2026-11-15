# Bongo Cat artwork

Original PNG sprites from [Gamma-Software/BongoCat-mac](https://github.com/Gamma-Software/BongoCat-mac),
revision `a1061e4592f83cd5a4f26ed85829a48181066d69`.

- `base.png`: upstream `Assets/resources/base.png`
- `left-*.png`, `right-*.png`: upstream `Assets/resources/Images/`
- Upstream MIT license retained in `LICENSE`.
- Bongo Cat character art: StrayRogue; original meme: DitzyFlama.

The cat has not been redrawn. The conversion script resamples the supplied
body and paw layers with Lanczos filtering on a 192×96 canvas. It stores each
layer once as a cropped, 256-color indexed image with an alpha palette.
The body is divided into three tiles, each at most 32 pixels high, to bound
individual decoded buffers to 24 KB. Only the paw images change while typing.
Upstream names are the **cat's** left/right: `right-down.png` is the paw on
the **viewer's left**. Firmware pose bits follow the viewer/keyboard sides.

Regenerate the checked-in LVGL I8 image arrays with Pillow installed:

```sh
python scripts/convert-bongo-cat.py
```

The script also writes `build/bongo-cat-preview.png` with all four poses at
native resolution. Source arrays use about 38 KB of flash, instead of the
original 221 KB of four duplicated full-color poses. LVGL uses its 48 KB heap
for UI objects and transient image decoding.
