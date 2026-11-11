import * as THREE from './vendor/three.module.js';
import { normalizePack } from './pack.js';

export async function loadArtwork(input) {
 const pack=normalizePack(input);
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
 const front=new THREE.CanvasTexture(canvas);
 front.colorSpace=THREE.SRGBColorSpace;
 return {front,radii,pack};
}
