import { createPrimaryPlayer } from "/runtime/ani-bot/player.js";

const STATES = [
  ["idle", "idle"],
  ["listening", "listening"],
  ["speaking/thinking", "streaming"],
  ["sleep", "sleeping"],
  ["burst", "finished"],
  ["failed", "failed"],
  ["notify", "notifying"],
  ["play", "playful"],
];

const LOOKS = [
  ["look-left", { yaw: -15, pitch: 0 }],
  ["look-up", { yaw: 0, pitch: 8 }],
  ["look-right", { yaw: 15, pitch: 0 }],
  ["look-down", { yaw: 0, pitch: -8 }],
  ["idle", null, "idle"],
];

const ENGINE_STATES = [
  ["sleeping", "sleeping"],
  ["listening", "listening"],
  ["streaming", "streaming"],
];

const packsSelect = document.getElementById("packs");
const stage = document.getElementById("stage");
const gallery = document.getElementById("gallery");
const evidence = document.getElementById("evidence");
const status = document.getElementById("status");
const stateLabel = document.getElementById("state-label");
const yawNode = document.getElementById("yaw");
const pitchNode = document.getElementById("pitch");
const fileInput = document.getElementById("file");
const drop = document.getElementById("drop");
const license = document.getElementById("license");
const probeNode = document.getElementById("probe");
const probeJson = document.getElementById("probe-json");
const sourceImg = document.getElementById("source-img");
const canonicalImg = document.getElementById("canonical-img");

let live;
let currentPack = null;
let look = null;
let currentState = "idle";
let clock = 0.8;
let last = performance.now();
let paused = false;
let reduced = false;
let raf = 0;
let evidenceLog = {};
let disposedFlag = false;
let lastPaintCount = 0;

function setStatus(ok, text) {
  status.dataset.ok = String(ok);
  status.textContent = text;
}

function pointerLook(event, box) {
  const clamp = (value) => Math.max(-1, Math.min(1, value));
  return {
    yaw: clamp((event.clientX - box.left - box.width / 2) / (box.width * 0.65)) * 15,
    pitch: -clamp((event.clientY - box.top - box.height / 2) / (box.height * 0.65)) * 8,
  };
}

stage.addEventListener("pointermove", (event) => {
  if (event.pointerType !== "mouse" || paused || reduced) return;
  look = pointerLook(event, stage.getBoundingClientRect());
  yawNode.textContent = look.yaw.toFixed(1);
  pitchNode.textContent = look.pitch.toFixed(1);
});
stage.addEventListener("pointerleave", () => {
  if (paused || reduced) return;
  look = null;
  yawNode.textContent = "0";
  pitchNode.textContent = "0";
});

function currentProbe(extra = {}) {
  const probe = live?.getProbe() ?? {};
  if (typeof probe.paintCount === "number") lastPaintCount = probe.paintCount;
  return {
    pack: currentPack?.id ?? null,
    paused,
    reduced,
    ...probe,
    evidence: evidenceLog,
    paintCount: probe.paintCount ?? lastPaintCount,
    packEyes: currentPack?.eyes ?? null,
    ...extra,
    disposed: disposedFlag,
    live: live != null,
  };
}

function writeProbe(extra = {}) {
  const probe = currentProbe(extra);
  const text = JSON.stringify(probe);
  probeNode.textContent = JSON.stringify(probe, null, 2);
  probeJson.textContent = text;
}

function embeddedPacks() {
  return globalThis.__ILLUSTRATED_PACKS ?? null;
}

async function publishProbe(extra = {}) {
  writeProbe(extra);
  if (globalThis.__ILLUSTRATED_OFFLINE) return;
  try {
    await fetch("/probe", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: probeJson.textContent,
    });
  } catch {
    // file:// and the offline HTML have no probe endpoint
  }
}

function tick(now) {
  raf = requestAnimationFrame(tick);
  if (paused || !live) {
    writeProbe();
    return;
  }
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  clock += dt;
  const nextLook = reduced ? null : look;
  live.paint(clock, currentState, 1, nextLook, reduced);
  writeProbe();
}
const params = new URLSearchParams(location.search);
const once = params.has("once");
if (!once) raf = requestAnimationFrame(tick);

function fillAnchors(pack) {
  const [left, right] = pack.eyes;
  document.getElementById("lx").value = left.x;
  document.getElementById("ly").value = left.y;
  document.getElementById("lrx").value = left.rx;
  document.getElementById("lry").value = left.ry;
  document.getElementById("rx").value = right.x;
  document.getElementById("ry").value = right.y;
  document.getElementById("rrx").value = right.rx;
  document.getElementById("rry").value = right.ry;
}

function readAnchors(pack) {
  const number = (id) => Number(document.getElementById(id).value);
  return {
    ...pack,
    eyes: [
      { x: number("lx"), y: number("ly"), rx: number("lrx"), ry: number("lry") },
      { x: number("rx"), y: number("ry"), rx: number("rrx"), ry: number("rry") },
    ],
  };
}

function copyCanvas(source, label, parent) {
  const cell = document.createElement("div");
  cell.className = "cell";
  cell.dataset.shot = label;
  const shot = document.createElement("canvas");
  shot.width = source.width;
  shot.height = source.height;
  shot.style.cssText = "width:100%;height:100%;display:block";
  shot.getContext("2d").drawImage(source, 0, 0);
  const cap = document.createElement("span");
  cap.textContent = label;
  cap.style.cssText = "position:absolute;left:6px;bottom:4px;font-size:10px;color:#ccc";
  cell.append(shot, cap);
  parent.append(cell);
  return shot;
}

function dispatchPointer(kind) {
  const box = stage.getBoundingClientRect();
  const midX = box.left + box.width / 2;
  const midY = box.top + box.height / 2;
  const points = {
    "look-left": { x: box.left + 2, y: midY },
    "look-right": { x: box.right - 2, y: midY },
    "look-up": { x: midX, y: box.top + 2 },
    "look-down": { x: midX, y: box.bottom - 2 },
  };
  const point = points[kind];
  if (!point) return;
  stage.dispatchEvent(
    new PointerEvent("pointermove", {
      clientX: point.x,
      clientY: point.y,
      pointerType: "mouse",
      bubbles: true,
    }),
  );
}

function paintBurst(player, state, nextLook, frames = 12, holdHead = false, still = true) {
  const count = state === "sleeping" ? Math.max(frames, 24) : frames;
  let probe = player.getProbe();
  for (let i = 0; i < count; i++) {
    clock += 0.05;
    player.paint(clock, state, 1, nextLook, still, holdHead);
    probe = player.getProbe();
  }
  return probe;
}

function paintUntil(player, state, nextLook, holdHead, still, test, maxFrames) {
  let probe = player.getProbe();
  for (let i = 0; i < maxFrames; i++) {
    clock += 0.05;
    player.paint(clock, state, 1, nextLook, still, holdHead);
    probe = player.getProbe();
    if (test(probe)) return probe;
  }
  return probe;
}

function lidOf(probe) {
  return probe?.eyes?.[0]?.lid ?? 1;
}

function recordEvidence(label, probe) {
  evidenceLog[label] = {
    state: probe.state,
    look: probe.look,
    yaw: probe.yaw,
    pitch: probe.pitch,
    lockHead: probe.lockHead,
    blink: probe.blink,
    closeLids: false,
    eyes: probe.eyes,
  };
}

async function postShot(label, canvas) {
  if (globalThis.__ILLUSTRATED_OFFLINE) return;
  try {
    await fetch("/shot", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ pack: currentPack?.id ?? "unknown", label, png: canvas.toDataURL("image/png") }),
    });
  } catch {
    // offline HTML has no /shot
  }
}

async function captureEvidence(options = {}) {
  evidence.replaceChildren();
  gallery.replaceChildren();
  evidenceLog = {};
  const glCanvas = stage.querySelector("canvas");
  if (!live || !glCanvas) return;
  for (const [label, nextLook, state = "idle"] of LOOKS) {
    if (nextLook) dispatchPointer(label);
    else {
      look = null;
      yawNode.textContent = "0";
      pitchNode.textContent = "0";
    }
    // Keep look/idle tiles on an open clip frame so a mid-blink does not fake motion.
    const probe = paintUntil(
      live,
      state,
      look ?? nextLook,
      true,
      true,
      (sample) => lidOf(sample) > 0.9 && (sample.blink ?? 0) < 0.15,
      40,
    );
    const shot = copyCanvas(glCanvas, label, evidence);
    recordEvidence(label, probe);
    await postShot(label, shot);
  }
  const blinkProbe = paintUntil(
    live,
    "idle",
    null,
    true,
    false,
    (sample) =>
      sample.state === "idle" &&
      lidOf(sample) <= 0.25 &&
      (sample.blink ?? 0) > 0.4 &&
      sample.eyes?.[0]?.closed === true,
    120,
  );
  const blinkShot = copyCanvas(glCanvas, "closed", evidence);
  recordEvidence("closed", blinkProbe);
  await postShot("closed", blinkShot);
  look = null;
  yawNode.textContent = "0";
  pitchNode.textContent = "0";
  for (const [label, state] of ENGINE_STATES) {
    const still = state !== "sleeping";
    paintBurst(live, state, null, state === "sleeping" ? 24 : 12, true, still);
    const probe = live.getProbe();
    const shot = copyCanvas(glCanvas, label, evidence);
    recordEvidence(label, probe);
    await postShot(label, shot);
  }
  const stateList = options.looksOnly
    ? STATES.filter((item) => item[1] === "idle" || item[1] === "sleeping" || item[1] === "streaming")
    : STATES;
  for (const [label, state] of stateList) {
    paintBurst(live, state, null, 8);
    const cell = document.createElement("button");
    cell.className = "cell";
    cell.type = "button";
    cell.dataset.state = state;
    cell.setAttribute("aria-pressed", state === "idle" ? "true" : "false");
    cell.title = `${label} → ${state}`;
    const shot = document.createElement("canvas");
    shot.width = glCanvas.width;
    shot.height = glCanvas.height;
    shot.style.cssText = "width:100%;height:100%;display:block";
    shot.getContext("2d").drawImage(glCanvas, 0, 0);
    const cap = document.createElement("span");
    cap.textContent = `${label} → ${state}`;
    cap.style.cssText = "position:absolute;left:6px;bottom:4px;font-size:10px;color:#ccc";
    cell.append(shot, cap);
    gallery.append(cell);
    cell.addEventListener("click", () => {
      currentState = state;
      stateLabel.textContent = `${label} → ${state}`;
      for (const node of gallery.querySelectorAll("[data-state]"))
        node.setAttribute("aria-pressed", node === cell ? "true" : "false");
      if (live) {
        clock += 0.05;
        live.paint(clock, currentState, 1, reduced ? null : look, reduced);
        writeProbe();
      }
    });
  }
  paintBurst(live, "idle", null, 4);
}

async function loadPack(pack, options = {}) {
  disposedFlag = false;
  live?.dispose();
  stage.replaceChildren();
  live = pack == null ? await createPrimaryPlayer(stage) : await createPrimaryPlayer(stage, pack);
  currentPack = live.pack ?? pack ?? { id: "__default__" };
  if (pack == null) currentPack = { ...currentPack, id: "__default__" };
  currentState = "idle";
  stateLabel.textContent = "idle";
  if (currentPack.eyes) fillAnchors(currentPack);
  if (!options.skipEvidence) await captureEvidence({ looksOnly: options.looksOnly });
  document.documentElement.dataset.ready = "yes";
  await publishProbe({ ready: true });
}

async function fetchCatalog() {
  const embedded = embeddedPacks();
  let catalog;
  if (embedded) {
    catalog = {
      packs: Object.entries(embedded).map(([id, item]) => ({ id, ok: Boolean(item?.pack && item?.artworkUrl) })),
    };
  } else {
    try {
      catalog = await (await fetch("/catalog")).json();
    } catch {
      setStatus(
        false,
        "This page needs the local server (python3 serve.py or node serve.ts). Do not open demo/index.html with file://. Double-click illustrated-avatar-offline.html for offline playback of the four prepared packs.",
      );
      return { packs: [] };
    }
  }
  packsSelect.replaceChildren();
  for (const item of catalog.packs) {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.id}${item.ok ? "" : " (missing)"}`;
    option.disabled = !item.ok;
    packsSelect.append(option);
  }
  return catalog;
}

async function selectPack(id, options = {}) {
  if (id === "__default__") {
    sourceImg.src = "";
    canonicalImg.src = "";
    license.textContent = "Default PRIMARY_GRAY_PACK. createPrimaryPlayer(host) with no custom pack.";
    setStatus(true, "Loaded default gray pack (no custom fields).");
    await loadPack(undefined, options);
    return;
  }
  const embedded = embeddedPacks()?.[id];
  const body = embedded
    ? {
        ok: true,
        pack: embedded.pack,
        artworkUrl: embedded.artworkUrl,
        sourceUrl: embedded.sourceUrl,
        canonicalUrl: embedded.canonicalUrl,
      }
    : await (await fetch(`/pack/${encodeURIComponent(id)}`)).json();
  if (!body.ok) {
    setStatus(false, body.error ?? "Pack failed to load.");
    return;
  }
  sourceImg.src = body.sourceUrl ?? "";
  canonicalImg.src = body.canonicalUrl ?? body.artworkUrl;
  license.textContent = body.pack.license ? `${body.pack.license}. ${body.pack.alphaStatus ?? ""}` : "";
  setStatus(
    true,
    `Loaded ${body.pack.id}. tilt ${body.pack.tiltDeg}°. eyes (${body.pack.eyes[0].x},${body.pack.eyes[0].y}) (${body.pack.eyes[1].x},${body.pack.eyes[1].y}). ${body.pack.eyelessSource ?? ""}`,
  );
  await loadPack({ ...body.pack, artworkUrl: body.artworkUrl }, options);
}

packsSelect.addEventListener("change", () => {
  void selectPack(packsSelect.value);
});

document.getElementById("apply-eyes").addEventListener("click", async () => {
  if (!currentPack) return;
  await loadPack(readAnchors(currentPack));
  setStatus(true, "Applied manual eye anchors.");
});

document.getElementById("pause").addEventListener("click", () => {
  paused = !paused;
  document.getElementById("pause").setAttribute("aria-pressed", String(paused));
  void publishProbe();
});

document.getElementById("reduced").addEventListener("click", () => {
  reduced = !reduced;
  look = null;
  document.getElementById("reduced").setAttribute("aria-pressed", String(reduced));
  void publishProbe();
});

document.getElementById("cleanup").addEventListener("click", () => {
  disposedFlag = true;
  live?.dispose();
  live = null;
  stage.replaceChildren();
  gallery.replaceChildren();
  evidence.replaceChildren();
  cancelAnimationFrame(raf);
  document.documentElement.dataset.ready = "disposed";
  void publishProbe({ disposed: true });
  setStatus(true, "WebGL player disposed.");
});

async function upload(file) {
  if (globalThis.__ILLUSTRATED_OFFLINE) {
    setStatus(
      false,
      "Upload pack build is not in this HTML. Photograph-to-chibi conversion is not a browser step; it is an upstream GenerateImage skill step. Unzip the bundle, run python3 serve.py, then drop a stylized head. Use extract-eyes.py --correct when detection misses.",
    );
    return;
  }
  setStatus(true, `Building pack from ${file.name}…`);
  const data = new FormData();
  data.append("image", file);
  data.append("id", file.name.replace(/\.[^.]+$/, ""));
  const response = await fetch("/build", { method: "POST", body: data });
  const body = await response.json();
  if (!body.ok) {
    setStatus(false, `${body.code}: ${body.error}`);
    return;
  }
  await fetchCatalog();
  packsSelect.value = body.id;
  setStatus(true, `Built ${body.id} with generic extractor. tilt ${body.report.tiltDeg}°.`);
  sourceImg.src = body.artworkUrl;
  canonicalImg.src = body.artworkUrl;
  license.textContent = "Upload fallback. Anchors came from extract/build-pack, not a prepared art-worker file.";
  await loadPack({ ...body.pack, artworkUrl: body.artworkUrl });
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (file) void upload(file);
});
drop.addEventListener("dragover", (event) => event.preventDefault());
drop.addEventListener("drop", (event) => {
  event.preventDefault();
  const file = event.dataTransfer?.files?.[0];
  if (file) void upload(file);
});

const catalog = await fetchCatalog();
const frame = params.get("frame");
const mode = params.get("mode");
if (frame) document.body.dataset.frame = frame;
const initial = params.get("pack") ?? catalog.packs.find((item) => item.ok)?.id;
if (mode === "pause") paused = true;
if (mode === "reduced") {
  reduced = true;
  look = null;
}
if (initial) {
  packsSelect.value = initial === "__default__" ? "" : initial;
  await selectPack(initial, {
    skipEvidence:
      Boolean(frame) ||
      mode === "pause" ||
      mode === "reduced" ||
      mode === "cleanup" ||
      mode === "pause-seq" ||
      mode === "reduced-seq",
    looksOnly: once,
  });
  const shot = frame ?? params.get("shot");
  if (shot) {
    const item = LOOKS.find((entry) => entry[0] === shot);
    if (item) {
      currentState = item[2] ?? "idle";
      if (item[1]) dispatchPointer(shot);
      else look = null;
      live?.paint(2, currentState, 1, look ?? item[1], true, true);
      const glCanvas = stage.querySelector("canvas");
      if (glCanvas) await postShot(shot, glCanvas);
      await publishProbe({ frame: shot });
    }
  }
  if (mode === "pause-seq" && live) {
    for (let i = 0; i < 8; i += 1) {
      clock += 0.05;
      live.paint(clock, currentState, 1, look, false, false);
    }
    paused = true;
    document.getElementById("pause").setAttribute("aria-pressed", "true");
    const before = live.getProbe().paintCount;
    tick(performance.now());
    tick(performance.now() + 16);
    tick(performance.now() + 32);
    await publishProbe({
      mode: "pause-seq",
      paintCountBefore: before,
      paintCountAfter: live.getProbe().paintCount,
    });
  } else if (mode === "reduced-seq" && live) {
    reduced = true;
    look = null;
    document.getElementById("reduced").setAttribute("aria-pressed", "true");
    dispatchPointer("look-right");
    live.paint(clock + 0.2, currentState, 1, look, reduced, false);
    await publishProbe({ mode: "reduced-seq" });
  } else if (mode === "cleanup") {
    document.getElementById("cleanup").click();
  } else {
    await publishProbe({ mode: mode ?? "play", once });
  }
  if (once) cancelAnimationFrame(raf);
} else {
  setStatus(false, "No pack is ready. Drop a stylized head or import the four prepared cases.");
}

window.__avatarDemo = {
  setLook(next) {
    look = next;
  },
  setState(next) {
    currentState = next;
    stateLabel.textContent = next;
  },
  getLook() {
    return look;
  },
  getState() {
    return currentState;
  },
  getProbe() {
    return JSON.parse(probeJson.textContent || "{}");
  },
  pause() {
    paused = true;
  },
  reduceMotion() {
    reduced = true;
    look = null;
  },
  dispose() {
    document.getElementById("cleanup").click();
  },
};
