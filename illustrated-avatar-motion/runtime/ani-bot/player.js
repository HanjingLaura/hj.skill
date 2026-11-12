import { AnimationPlayer, StateDirector } from '../grok/core.js';
import { createSurface } from './surface.js';
import { eyeStroke, smoothEye } from './states.mjs';
import { normalizePack } from './pack.js';
import { bodyMotion } from './body-motion.js';

// Map StateDirector sleep and Idle_B clip lids onto the canvas stroke.
// grok `rl()` squashes stadium geometry but leaves lidY at 1; surface.js
// draws a closed line only when lid <= 0.25. Sleeping holds face "sleepy"
// (thin path, lidY 1) and suppresses clip blinks, so the canvas lid comes
// from the state name. Idle blinks come from frame.blink (Pe).
function canvasLid(stateName, blinkAmount, strokeLid) {
  if (stateName === 'sleeping' || stateName === 'drowsy') return 0.08;
  const blink = Math.max(0, Math.min(1, Number(blinkAmount) || 0));
  return Math.max(0.025, Math.min(1.3, strokeLid * (1 - blink)));
}

// Keep the supplied character's face. Symbol morphs belong to the generic avatars.
export async function createPrimaryPlayer(host, input) {
  const pack = normalizePack(input);
  const surface = await createSurface(host, input);
  let player = AnimationPlayer({ body: 'sphere', isGazeAlways: true });
  const restPlayer = AnimationPlayer({ body: 'sphere' });
  let director = StateDirector(player, 'idle', { seed: 120 });
  let state = 'idle', version = 0, previous = 0, yaw = 0, pitch = 0;
  let eyes = [null, null], gazeX = 0, gazeY = 0, lastLook = null, lastStill = false, lastStrokes = [];
  let motion={x:0,y:0,sx:1,sy:1};
  const canvas=host.querySelector("canvas");
  let paintCount = 0, disposed = false, lastLockHead = false, lastBlink = 0;
  return {
    pack,
    paint(time, next, nextVersion, look, still = false, lockHead = false) {
      if (disposed) return;
      paintCount += 1;
      lastLockHead = Boolean(lockHead);
      if (next !== state || nextVersion !== version) {
        if (next === state) {
          player = AnimationPlayer({ body: 'sphere', isGazeAlways: true });
          director = StateDirector(player, next, { seed: 120 });
        } else director.setState(next);
        state = next; version = nextVersion;
      }
      const dt = Math.min(.064, Math.max(0, time - previous));
      previous = time;
      player.setGaze(look ? [look.yaw / 15, look.pitch / 8] : null);
      if (!lockHead) director.advance(dt);
      player.setMorph(null);
      if (!lockHead) player.advance(dt);
      const frame = lockHead ? restPlayer.frame() : player.frame();
      motion=still||lockHead?{x:0,y:0,sx:1,sy:1}:bodyMotion(frame);
      // Pointer gaze and the upper-left idle pose use the same portrait scale.
      if (state === 'idle') motion = { ...motion, sx: 1, sy: 1 };
      canvas.style.transformOrigin='50% 50%';
      canvas.style.transform='translate('+motion.x+'%,'+motion.y+'%) scale('+motion.sx+','+motion.sy+')';
      lastBlink = lockHead ? 0 : Math.max(0, Math.min(1, Number(frame.blink) || 0));
      const blend = still ? 1 : 1 - Math.exp(-dt * 12);
      const headLook = look;
      yaw += ((headLook ? headLook.yaw / 15 * .35 : 0) - yaw) * blend;
      pitch += ((headLook ? headLook.pitch / 8 * .23 : 0) - pitch) * blend;
      const gazeBlend = still ? 1 : 1 - Math.exp(-dt * 18);
      gazeX += ((look && !lockHead ? look.yaw / 15 : 0) - gazeX) * gazeBlend;
      gazeY += ((look && !lockHead ? -look.pitch / 8 : 0) - gazeY) * gazeBlend;
      const strokes = [0, 1].map(i => {
        const eye = frame.eyes?.[i] ?? {};
        const valid = !((eye.pts && eye.pts.length < 2) || eye.wid <= 0);
        const stroke = smoothEye(eyes[i], eyeStroke(valid ? eye : {}), dt, still);
        const drawn = { ...stroke, lid: canvasLid(state, lastBlink, stroke.lid) };
        eyes[i] = drawn;
        const following = look || Math.abs(gazeX) + Math.abs(gazeY) > .001;
        return { ...drawn, gazeX: following ? gazeX * 12 : (eye.off?.[0] ?? 0) * 40,
          gazeY: following ? gazeY * 8 : -(eye.off?.[1] ?? 0) * 40 };
      });
      lastLook = look;
      lastStill = still;
      lastStrokes = strokes;
      surface.draw(yaw, pitch, strokes, null, dt);
    },
    getProbe() {
      return {
        state,
        still: lastStill,
        look: lastLook,
        yaw,
        pitch,
        gazeX,
        gazeY,
        blink: lastBlink,
        motion,
        paintCount,
        disposed,
        lockHead: lastLockHead,
        eyes: lastStrokes.map((stroke) => {
          const lid = Number.isFinite(stroke.lid) ? stroke.lid : 1;
          return {
            gazeX: stroke.gazeX ?? 0,
            gazeY: stroke.gazeY ?? 0,
            lid,
            width: stroke.width ?? 0,
            tilt: stroke.tilt ?? 0,
            closed: lid <= 0.25,
            pointCount: Array.isArray(stroke.points) ? stroke.points.length : 0,
          };
        }),
      };
    },
    dispose() { disposed = true; surface.dispose(); },
  };
}
