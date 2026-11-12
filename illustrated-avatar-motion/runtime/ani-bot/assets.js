import * as THREE from './vendor/three.module.js';
import { normalizePack } from './pack.js';

const preparedArtwork = new Map();
const cacheLimit = 8;

async function cachedArtwork(pack) {
 const key=JSON.stringify([pack.artworkUrl,pack.canvas,pack.cropWidth,pack.floodAlpha,pack.silhouetteAlpha,pack.floodSeed?.[0]??.5,pack.floodSeed?.[1]??.5]);
 let pending=preparedArtwork.get(key);
 if (!pending) {
  pending=prepareArtwork(pack).catch(error => {
   if (preparedArtwork.get(key) === pending) preparedArtwork.delete(key);
   throw error;
  });
 }
 preparedArtwork.delete(key);
 preparedArtwork.set(key,pending);
 if (preparedArtwork.size > cacheLimit) preparedArtwork.delete(preparedArtwork.keys().next().value);
 return pending;
}

export async function artworkEyePaint(input) {
 const pack = normalizePack(input);
 const {canvas} = await cachedArtwork(pack);
 return input.eyePaint || contrastingEyePaint(canvas, pack);
}

export async function loadArtwork(input) {
 const pack = normalizePack(input);
 const {canvas,radii} = await cachedArtwork(pack);
 // A disposed avatar must not dispose another avatar's GPU texture.
 const front=new THREE.CanvasTexture(canvas);
 front.colorSpace=THREE.SRGBColorSpace;
 const eyePaint = input.eyePaint || contrastingEyePaint(canvas, pack);
 return {front,radii:radii.slice(),pack,eyePaint};
}

function contrastingEyePaint(canvas, pack) {
 const context = canvas.getContext('2d');
 let luminance = 0;
 let samples = 0;
 for (const eye of pack.eyes) {
  const x = Math.max(0, Math.min(canvas.width - 5, Math.round(eye.x / 100 * canvas.width) - 2));
  const y = Math.max(0, Math.min(canvas.height - 5, Math.round(eye.y / 100 * canvas.height) - 2));
  const pixels = context.getImageData(x, y, 5, 5).data;
  for (let offset = 0; offset < pixels.length; offset += 4) {
   if (pixels[offset + 3] < 180) continue;
   luminance += 0.2126 * pixels[offset] + 0.7152 * pixels[offset + 1] + 0.0722 * pixels[offset + 2];
   samples++;
  }
 }
 // Reserve white eyes for near-black faces. Medium gray fur keeps dark eyes.
 return samples && luminance / samples < 65 ? '#ffffff' : pack.eyePaint;
}

async function prepareArtwork(pack) {
 const image=await new THREE.ImageLoader().loadAsync(pack.artworkUrl);
 const size=pack.canvas,canvas=document.createElement('canvas');
 canvas.width=canvas.height=size;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 const srcW=image.width>=image.height*1.8?Math.min(pack.cropWidth,image.width):image.width;
 const srcH=image.height;
 const scale=srcH>size?size/srcH:1;
 const drawW=srcW*scale,drawH=srcH*scale;
 ctx.drawImage(image,0,0,srcW,srcH,(size-drawW)/2,(size-drawH)/2,drawW,drawH);
 const frame=ctx.getImageData(0,0,size,size),pixels=frame.data;
 const queue=new Int32Array(size*size),seen=new Uint8Array(size*size);
 let tail=0;
 function add(k){
  const p=k*4;
  if(seen[k]||pixels[p+3]<pack.floodAlpha)return;
  seen[k]=1;queue[tail++]=k;
 }
 const seedX=Math.round(size*(pack.floodSeed?.[0]??.5));
 const seedY=Math.round(size*(pack.floodSeed?.[1]??.5));
 add(seedY*size+seedX);
 for(let head=0;head<tail;head++){
  const k=queue[head],x=k%size;
  if(x>0)add(k-1);if(x<size-1)add(k+1);
  if(k>=size)add(k-size);if(k<size*(size-1))add(k+size);
 }
 for(let k=0;k<seen.length;k++)if(!seen[k])pixels[k*4+3]=0;
 ctx.putImageData(frame,0,0);
 const half=size/2;
 const radii=Array.from({length:256},(_,i)=>{
  const angle=i/256*Math.PI*2;
  for(let r=half-2;r>0;r--){
   const x=Math.round(half+r*Math.cos(angle)),y=Math.round(half+r*Math.sin(angle));
   if(pixels[(y*size+x)*4+3]>pack.silhouetteAlpha)return r/size*400;
  }
  return 140;
 });
 return {canvas,radii};
}
