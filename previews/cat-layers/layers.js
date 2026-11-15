/* Layer-specific props, drawn around the original cat sprites. */
"use strict";
const layers = {
  base: ["Base", "all paws on deck", "HYPERSPACE: MEOW"],
  number: ["Number", "counting on my paws", "carry the tuna"],
  arrows: ["Arrows", "ready for takeoff", "captain whiskers"],
  mouse: ["Mouse", "stay right there...", "almost had it!"],
  functions: ["Functions", "a little purrcery", "special powers!"],
  system: ["System", "mission control", "all systems purring"],
  brackets: ["Brackets", "if I fits, I sits", "{ snug as a cat }"],
  nomods: ["No Mods", "just my type", "letters, paw by paw"],
  recsel: ["RecSel", "which reel? ?", "ready when you are"],
  playsel: ["PlaySel", "pick a mixtape ?", "encore?"],
  recording: ["Recording", "saving every paw", "tape is rolling"],
};
function box(x, y, w, h, fill, stroke = ink) {
  path(c => c.rect(x, y, w, h), fill, stroke);
}
function line(x, y, ex, ey, color = ink, width = 2) {
  path(c => { c.moveTo(x, y); c.lineTo(ex, ey); }, null, color, width);
}
function sparkle(x, y, size, color) {
  line(x - size, y, x + size, y, color, 1.5);
  line(x, y - size, x, y + size, color, 1.5);
}
function tape(x, y, running, small = false) {
  const w = small ? 43 : 74, h = small ? 22 : 28;
  box(x, y, w, h, "#52657f");
  const r = small ? 6 : 8;
  for (const cx of [x + w * 0.27, x + w * 0.73]) {
    ellipse(cx, y + h / 2, r, r, "#111e30", "#afbdd2");
    const angle = running ? time * 6 : 0;
    line(cx, y + h / 2, cx + Math.cos(angle) * (r - 2), y + h / 2 + Math.sin(angle) * (r - 2), "#afbdd2", 1);
  }
  line(x + w * 0.27, y + h / 2 + r, x + w * 0.73, y + h / 2 + r, "#afbdd2", 1);
}
function accessories(layer, sleeping, active) {
  if (layer === "number") {
    ellipse(81, 149, 12, 10, null, "#546981");
    ellipse(138, 153, 12, 10, null, "#546981");
    line(93, 149, 126, 152, "#546981");
  }
  if (layer === "functions") {
    path(c => { c.moveTo(91, 119); c.lineTo(109, 92); c.lineTo(132, 119); c.closePath(); }, "#8b6aca");
    ellipse(111, 119, 27, 4, "#9977de", ink);
    sparkle(109, 105, 3, "#ffe396");
  }
  if (layer === "system") {
    path(c => c.arc(120, 133, 43, Math.PI, Math.PI * 2), null, "#52657f", 5);
    box(74, 126, 10, 21, "#55b9cd"); box(156, 126, 10, 21, "#55b9cd");
    line(160, 145, 139, 151, "#52657f", 3);
    ellipse(137, 151, 4, 2, ink);
  }
  if (layer === "arrows") {
    const directions = [[0, -1], [1, 0], [0, 1], [-1, 0]];
    directions.forEach(([dx, dy], i) => {
      const x = 205 + dx * 10, y = 120 + dy * 10;
      const color = !sleeping && Math.floor(time * (active ? 4 : 1)) % 4 === i ? "#ffd879" : "#40566e";
      line(x - dx * 4, y - dy * 4, x + dx * 3, y + dy * 3, color);
      line(x + dx * 3, y + dy * 3, x - dy * 3, y + dx * 3, color);
      line(x + dx * 3, y + dy * 3, x + dy * 3, y - dx * 3, color);
    });
  }
}
function props(layer, sleeping, active, paws) {
  const motion = sleeping ? 0 : time;
  const pulse = active || paws.some(p => p > 0);
  switch (layer) {
    case "base":
      for (const x of [77, 157]) {
        box(x - 24, 168, 48, 18, "#b76a4d");
        ellipse(x, 168, 24, 5, "#f3d7a8", ink);
        line(x - 16, 173, x - 12, 184, "#edd1a5");
        line(x + 16, 173, x + 12, 184, "#edd1a5");
      }
      break;
    case "number":
      box(94, 155, 53, 34, "#6f9c9a");
      box(100, 158, 41, 9, "#d9edbc");
      text(pulse ? String(Math.floor(motion * 7) % 100) : "2 + 2", 120, 166, ink, 8);
      for (let i = 0; i < 12; i++) box(101 + i % 4 * 10, 171 + Math.floor(i / 4) * 5, 6, 3, pulse && Math.floor(time * 10) % 12 === i ? "#ffd879" : "#dce6df", null);
      if (!sleeping) ["+", "−", "="].forEach((s, i) => text(s, 57 + i * 61, 123 - (motion * 9 + i * 7) % 22, "#ffd879", 13));
      break;
    case "arrows": {
      box(72, 177, 98, 12, "#4a647c");
      const tilt = Math.sin(motion * (pulse ? 7 : 2)) * 9;
      line(120, 180, 120 + tilt, 161, "#9fb0c4", 5);
      ellipse(120 + tilt, 160, 7, 5, "#e69884", ink);
      ellipse(151, 181, 4, 3, pulse ? "#ffd879" : cyan);
      break;
    }
    case "functions": {
      const y = 153 + Math.sin(motion * 5) * 3;
      line(158, 171, 185, y, "#e6c991", 3);
      ellipse(185, y, 3, 3, "#ffd879");
      if (!sleeping) for (let i = 0; i < 5; i++) {
        const phase = (motion * (pulse ? 2 : 0.6) + i / 5) % 1;
        sparkle(185 + Math.sin(i * 4) * phase * 22, y - phase * 32, 2 * (1 - phase), i % 2 ? cyan : "#ffd879");
      }
      break;
    }
    case "system":
      box(67, 163, 108, 26, "#40566e");
      for (let i = 0; i < 4; i++) {
        ellipse(81 + i * 25, 176, 6, 6, "#9bb0c4", ink);
        const angle = motion * (pulse ? 5 : 0.5) + i;
        line(81 + i * 25, 176, 81 + i * 25 + Math.sin(angle) * 4, 176 - Math.cos(angle) * 4, ink, 1);
        ellipse(81 + i * 25, 167, 1.5, 1.5, !sleeping && Math.floor(time * 3 + i) % 2 ? "#ffd879" : "#55b9cd");
      }
      break;
    case "brackets": {
      const squeeze = pulse ? Math.sin(motion * 6) * 3 : 0;
      box(78 + squeeze, 163, 84 - squeeze * 2, 25, "#b9895e");
      path(c => { c.moveTo(78, 163); c.lineTo(65, 153); c.lineTo(102, 158); c.lineTo(120, 163);
        c.lineTo(143, 158); c.lineTo(176, 153); c.lineTo(162, 163); }, "#d6ac7b");
      text("{", 72 + squeeze, 183, "#ffe4be", 31);
      text("}", 168 - squeeze, 183, "#ffe4be", 31);
      text("CAT", 120, 180, "#68482f", 9);
      break;
    }
    case "nomods": {
      const carriage = pulse ? (Math.floor(motion * 8) % 16) - 8 : 0;
      box(96 + carriage, 151, 49, 24, "#fff4dc");
      for (let i = 0; i < 3; i++) line(102 + carriage, 156 + i * 5, 111 + carriage + (pulse ? Math.floor(motion * 12 + i * 7) % 26 : 20), 156 + i * 5, "#7b8697", 1);
      box(78, 172, 86, 17, "#60968e");
      line(76 + carriage, 170, 166 + carriage, 170, "#a6b9c5", 4);
      for (let i = 0; i < 18; i++) ellipse(86 + i % 9 * 8, 178 + Math.floor(i / 9) * 6, 2, 2, pulse && Math.floor(time * 10) % 18 === i ? "#ffd879" : white);
      break;
    }
    case "recsel":
      box(87, 162, 68, 27, "#28384d");
      ctx.save(); ctx.translate(87, 162); ctx.rotate(sleeping ? 0 : -0.18 - Math.abs(Math.sin(motion * 2)) * 0.22);
      box(0, -7, 68, 7, "#edf0ed");
      for (let i = 0; i < 6; i++) line(4 + i * 12, -7, 9 + i * 12, 0, ink, 4);
      ctx.restore();
      text("REC  ?", 121, 181, white, 13);
      break;
    case "playsel":
      tape(83, 157, false);
      text("?", 120, 175, "#ffd879", 14);
      path(c => { c.moveTo(117, 180); c.lineTo(117, 189); c.lineTo(125, 184.5); c.closePath(); }, !sleeping && Math.floor(time * 2) % 2 ? "#ffd879" : cyan, null);
      break;
    case "recording":
      tape(83, 160, !sleeping);
      break;
  }
}
function recordingBadge(sleeping) {
  tape(179, 150, !sleeping, true);
  ellipse(185, 144, 2.5, 2.5, Math.floor(time * 2) % 2 ? "#ff637e" : "#763548");
  text("REC", 205, 147, "#ff8295", 8);
}
