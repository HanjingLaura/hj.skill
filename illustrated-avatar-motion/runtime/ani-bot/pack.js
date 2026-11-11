export const PRIMARY_GRAY_PACK = {
  id: 'primary-gray',
  canvas: 744,
  cropWidth: 744,
  tiltDeg: 20,
  eyes: [
    { x: 37.47, y: 57.83, rx: 3.5, ry: 6.6 },
    { x: 57.75, y: 62.73, rx: 3.5, ry: 6.6 },
  ],
  rim: '#b9bbbd',
  eyePaint: '#1c1c25',
  floodAlpha: 100,
  silhouetteAlpha: 180,
  uvOrigin: 8,
  uvSize: 84,
  headDepth: 19,
  rebuildDepth: 9,
  eyeExtent: 14.74,
  chinSmooth: { fadeIn: [0, 18], fadeOut: [42, 62], radius: 7, mix: 0.8 },
}

export function defaultArtworkUrl() {
  return ""
}

export function normalizePack(input = {}) {
  const eyes = Array.isArray(input.eyes) && input.eyes.length >= 2 ? input.eyes : PRIMARY_GRAY_PACK.eyes
  const left = eyeOf(eyes[0], PRIMARY_GRAY_PACK.eyes[0])
  const right = eyeOf(eyes[1], PRIMARY_GRAY_PACK.eyes[1])
  const canvas = numberOf(input.canvas, PRIMARY_GRAY_PACK.canvas)
  const uvSize = numberOf(input.uvSize, PRIMARY_GRAY_PACK.uvSize)
  const pack = {
    ...PRIMARY_GRAY_PACK,
    ...input,
    canvas,
    cropWidth: numberOf(input.cropWidth, canvas),
    tiltDeg: numberOf(input.tiltDeg, PRIMARY_GRAY_PACK.tiltDeg),
    eyes: [left, right],
    rim: typeof input.rim === 'string' && input.rim ? input.rim : PRIMARY_GRAY_PACK.rim,
    eyePaint: typeof input.eyePaint === 'string' && input.eyePaint ? input.eyePaint : PRIMARY_GRAY_PACK.eyePaint,
    floodAlpha: numberOf(input.floodAlpha, PRIMARY_GRAY_PACK.floodAlpha),
    silhouetteAlpha: numberOf(input.silhouetteAlpha, PRIMARY_GRAY_PACK.silhouetteAlpha),
    uvOrigin: numberOf(input.uvOrigin, PRIMARY_GRAY_PACK.uvOrigin),
    uvSize,
    headDepth: numberOf(input.headDepth, PRIMARY_GRAY_PACK.headDepth),
    rebuildDepth: numberOf(input.rebuildDepth, PRIMARY_GRAY_PACK.rebuildDepth),
    eyeExtent: numberOf(input.eyeExtent, PRIMARY_GRAY_PACK.eyeExtent),
    chinSmooth: input.chinSmooth === null || input.chinSmooth === false ? null : (input.chinSmooth ?? PRIMARY_GRAY_PACK.chinSmooth),
    artworkUrl: typeof input.artworkUrl === 'string' && input.artworkUrl ? input.artworkUrl : defaultArtworkUrl(),
  }
  pack.borderWidth = uvSize / canvas
  pack.tiltRad = pack.tiltDeg * Math.PI / 180
  return pack
}

function numberOf(value, fallback) {
  return Number.isFinite(value) ? Number(value) : fallback
}

function eyeOf(value, fallback) {
  return {
    x: numberOf(value?.x, fallback.x),
    y: numberOf(value?.y, fallback.y),
    rx: numberOf(value?.rx, fallback.rx),
    ry: numberOf(value?.ry, fallback.ry),
  }
}
