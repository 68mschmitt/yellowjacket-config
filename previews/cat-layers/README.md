# Cat layer animation study

Open `index.html` in a desktop browser. No build, server, or dependencies needed.

The preview tours all eleven layers, spending 18 seconds on each: 6 seconds idle,
6 seconds active, 6 seconds sleeping. The layer picker isolates any animation.
Both views render the same 240×240 canvas at 10 fps.
Status values are illustrative; browser fonts approximate the display layout.

Select a scene to inspect it, change speed, or pause. In Interactive mode, A/L
or the paw buttons trigger left/right swats. After 15 seconds without input,
the cat sleeps with its layer props. Input wakes it again. Paw input during the
tour locks onto the currently visible layer. The recording checkbox previews a
recording overlay on any layer.

Scenes: bongo cat / hyperspace, calculator and glasses, pilot and flight stick,
mouse hunt, wizard and wand, headset and console, bracket box, typewriter,
record-selection clapperboard, playback-selection cassette, and recording reels.

The cat uses the original body and four up/down paw PNGs directly from
`src/display/assets/bongo_cat/`, at the firmware's 192×96 size. Keep the preview
inside the repository so these relative paths resolve. Attribution and license
are in that asset directory. Props and accessories are Canvas overlays; moving
paws render above them. Catnaps use lowered paws, gentle breathing, and floating
Zs, preserving the original face.

This preview does not change firmware or produce firmware-ready sprites yet.
