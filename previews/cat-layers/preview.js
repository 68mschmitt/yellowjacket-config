/* Original bongo cat sprites with layer-specific Canvas 2D overlays. */
"use strict";
const canvas = document.querySelector("#large");
const ctx = canvas.getContext("2d");
const native = document.querySelector("#actual").getContext("2d");
const mode = document.querySelector("#mode");
const speed = document.querySelector("#speed");
const stateLabel = document.querySelector("#state");
const layerPicker = document.querySelector("#layer");
const record = document.querySelector("#record");
let time = 0, previous = 0, lastFrame = -1, paused = false, lastInput = 0;
let hits = [-100, -100];
const ink = "#172132", white = "#fffcff", cyan = "#55ddff";
const sprites = {};
let assetsReady = false;
const assetsLoaded = Promise.all(["base", "right-up", "right-down", "left-up", "left-down"].map(name =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => { sprites[name] = image; resolve(); };
    image.onerror = () => reject(new Error(`Could not load ${name}.png`));
    image.src = `../../src/display/assets/bongo_cat/${name}.png`;
  })
));

function catSprite(name) {
  // Same dimensions and alignment as the firmware's original sprite layers.
  ctx.drawImage(sprites[name], 24, 92, 192, 96);
}

function path(points, fill, stroke = ink, width = 2) {
  ctx.beginPath();
  points(ctx);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.stroke(); }
}
function ellipse(x, y, rx, ry, fill, stroke = null) {
  path(c => c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2), fill, stroke);
}
function text(value, x, y, color, size = 14) {
  ctx.fillStyle = color; ctx.font = `${size}px sans-serif`; ctx.textAlign = "center";
  ctx.fillText(value, x, y);
}
function paw(side, progress, sleeping) {
  // Upstream names are anatomical: right is screen-left.
  const name = side ? "left" : "right";
  const down = sleeping || (progress >= 0.2 && progress < 0.8);
  catSprite(`${name}-${down ? "down" : "up"}`);
}
function drawMouse(x, y, direction, sleeping) {
  ctx.save(); ctx.translate(x, y); ctx.scale(direction, 1);
  path(c => { c.moveTo(-10, 1); c.bezierCurveTo(-23, 6, -27, -8, -32, -2); }, null, "#e9a6b6", 1.5);
  ellipse(0, 0, 11, 6, "#aab8d0", ink);
  path(c => { c.moveTo(5, -5); c.lineTo(17, 2); c.lineTo(5, 5); }, "#aab8d0");
  ellipse(4, -6, 4, 5, "#d1d9e8", ink);
  ellipse(4, -6, 2, 3, "#e9a6b6");
  ellipse(11, -1, 1, 1, ink);
  ellipse(17, 2, 1.5, 1.5, "#edb0c0");
  if (!sleeping) {
    path(c => { c.moveTo(-5, 5); c.lineTo(-7 + Math.sin(time * 24) * 2, 8);
      c.moveTo(5, 5); c.lineTo(7 - Math.sin(time * 24) * 2, 8); }, null, "#d1d9e8", 1.5);
  }
  ctx.restore();
}
function render() {
  if (!assetsReady) return;
  const layer = layerPicker.value === "tour" ? Object.keys(layers)[Math.floor(time / 18) % Object.keys(layers).length] : layerPicker.value;
  const [name, idleCaption, activeCaption] = layers[layer];
  const cycle = time % 18;
  let scene = mode.value;
  if (scene === "demo") scene = cycle < 6 ? "hunt" : cycle < 12 ? "swat" : "sleep";
  if (scene === "interactive") scene = time - lastInput >= 15 ? "sleep" : "hunt";
  const sleeping = scene === "sleep";
  const active = scene === "swat";
  const mouseX = sleeping ? 169 : 120 + Math.sin(time * 1.8) * 57;
  const direction = Math.cos(time * 1.8) >= 0 ? 1 : -1;
  const pawStates = hits.map(t => time - t >= 0 && time - t < 0.5 ? (time - t) / 0.5 : 0);
  if (scene === "swat") {
    const beat = time % (layer === "mouse" ? 1.2 : 0.6);
    const side = layer === "mouse" ? (mouseX < 120 ? 0 : 1) : Math.floor(time / 0.6) % 2;
    if (beat < 0.5) pawStates[side] = beat / 0.5;
  }
  ctx.fillStyle = "#07101c"; ctx.fillRect(0, 0, 240, 240);
  for (let i = 0; i < 16; i++) {
    const angle = i * Math.PI / 8;
    const radius = 35 + (i * 17 + time * 2) % 77;
    const x = 120 + Math.cos(angle) * radius, y = 120 + Math.sin(angle) * radius;
    if (layer === "base" && active) line(x, y, x + Math.cos(angle) * 9, y + Math.sin(angle) * 9, "#63bace", 1);
    else ellipse(x, y, 1, 1, "#264354");
  }
  text(name, 120, 26, cyan);
  text(active ? "92 WPM" : "0 WPM", 120, 50, white, 20);
  text("1200 DPI", 120, 70, cyan);
  text("USB ready", 80, 87, white, 12); text("2/2 linked", 175, 87, white, 12);
  ellipse(120, 177, 73, 6, "#030a13");
  ctx.save();
  ctx.translate(sleeping ? 0 : Math.sin(time * 1.8) * 2, Math.sin(time * (sleeping ? 2 : 4)) * (sleeping ? 1 : 0.6));
  catSprite("base");
  accessories(layer, sleeping, active);
  // Resting paws sit behind props; moving paws are composited above them below.
  for (let side = 0; side < 2; side++) {
    if (pawStates[side] === 0) paw(side, 0, sleeping);
  }
  ctx.restore();
  props(layer, sleeping, active, pawStates);
  if (layer === "mouse") drawMouse(mouseX, sleeping ? 179 : 179 + Math.sin(time * 18) * 0.7, sleeping ? -1 : direction, sleeping);
  if (record.checked || layer === "recording") recordingBadge(sleeping);
  ctx.save();
  ctx.translate(sleeping ? 0 : Math.sin(time * 1.8) * 2, Math.sin(time * (sleeping ? 2 : 4)) * (sleeping ? 1 : 0.6));
  for (let side = 0; side < 2; side++) {
    if (pawStates[side] > 0) paw(side, pawStates[side], sleeping);
  }
  ctx.restore();
  if (sleeping) text("z Z", 185, 113 - (time % 2) * 4, cyan, 12);
  if (pawStates.some(p => p > 0.35 && p < 0.75)) {
    const x = pawStates[0] > 0 ? 63 : 177;
    path(c => { c.moveTo(x - 8, 176); c.lineTo(x - 12, 172);
      c.moveTo(x + 8, 176); c.lineTo(x + 12, 172); }, null, "#ffd879", 1.5);
  }
  text(sleeping ? (layer === "mouse" ? "truce until further notice" : "catnap on the job") : active || pawStates.some(p => p > 0) ? activeCaption : idleCaption, 120, 203, "#ffd879", 12);
  text("L 85%     R 92%", 120, 224, white, 12);
  native.clearRect(0, 0, 240, 240); native.drawImage(canvas, 0, 0);
  const label = `${paused ? "Paused · " : ""}${name} · ${sleeping ? "Catnap" : active || pawStates.some(p => p > 0) ? "Active" : "Idle"}${layerPicker.value === "tour" ? " · next layer in " + Math.ceil(18 - cycle) + "s" : ""}`;
  if (stateLabel.textContent !== label) stateLabel.textContent = label;
}
function hit(side) {
  if (layerPicker.value === "tour") layerPicker.value = Object.keys(layers)[Math.floor(time / 18) % Object.keys(layers).length];
  if (mode.value !== "interactive") mode.value = "interactive";
  lastInput = time; hits[side] = time; render();
}
document.querySelector("#left").onclick = () => hit(0);
document.querySelector("#right").onclick = () => hit(1);
document.querySelector("#pause").onclick = event => {
  paused = !paused; event.target.textContent = paused ? "Play" : "Pause"; render();
};
mode.onchange = () => { time = 0; lastInput = 0; hits = [-100, -100]; render(); };
layerPicker.onchange = mode.onchange;
record.onchange = render;
document.addEventListener("keydown", event => {
  if (event.target.matches("select, button, input") || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.key.toLowerCase() === "a") hit(0);
  if (event.key.toLowerCase() === "l") hit(1);
});
function tick(now) {
  const delta = previous ? Math.min((now - previous) / 1000, 0.1) : 0;
  previous = now;
  if (!paused) time += delta * Number(speed.value);
  const frame = Math.floor(time * 10);
  if (frame !== lastFrame) { lastFrame = frame; render(); }
  requestAnimationFrame(tick);
}
stateLabel.textContent = "Loading original cat artwork…";
assetsLoaded.then(() => {
  assetsReady = true;
  if (new URLSearchParams(location.search).has("export")) {
    const frames = {};
    for (const layer of Object.keys(layers)) {
      frames[layer] = [];
      for (let phase = 0; phase < 2; phase++) {
        time = phase ? 0.35 : 0;
        ctx.clearRect(0, 0, 240, 240);
        accessories(layer, false, !!phase);
        props(layer, false, !!phase, [0, 0]);
        frames[layer].push(canvas.toDataURL());
      }
    }
    for (const name of ["mouse_sprite", "record_badge"]) {
      frames[name] = [];
      for (let phase = 0; phase < 2; phase++) {
        time = phase * 0.5;
        ctx.clearRect(0, 0, 240, 240);
        if (name === "mouse_sprite") drawMouse(120, 179, phase ? -1 : 1, false);
        else recordingBadge(false);
        frames[name].push(canvas.toDataURL());
      }
    }
    const output = document.createElement("pre");
    output.id = "exported-frames";
    output.textContent = JSON.stringify(frames);
    document.body.append(output);
    return;
  }
  render();
  requestAnimationFrame(tick);
}).catch(error => { stateLabel.textContent = `${error.message}. Keep the preview inside the repository so its asset paths resolve.`; });
