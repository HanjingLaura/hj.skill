import * as THREE from './vendor/three.module.js';
import {loadArtwork} from './assets.js';
import {normalizePack} from './pack.js';
// A continuous surface sampled from the inferred volume. Pack anchors replace
// the original hardcoded eye cutouts so another illustrated head can reuse it.
export async function createSurface(host, input){
 const pack=normalizePack(input);
 const {front,radii:sourceRadii}=await loadArtwork(pack);
 const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});renderer.setPixelRatio(Math.min(Math.max(devicePixelRatio,2),3));renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.domElement.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none';host.append(renderer.domElement);
 const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-50,50,50,-50,.1,400);camera.position.z=200;
 const group=new THREE.Group();scene.add(group);scene.add(new THREE.AmbientLight(0xffffff,1.5));const light=new THREE.DirectionalLight(0xfff6f0,2);light.position.set(-70,100,120);scene.add(light);
 const baseRadii=sourceRadii.map((r,i)=>(
  sourceRadii[(i+254)%256]+4*sourceRadii[(i+255)%256]+6*r+
  4*sourceRadii[(i+1)%256]+sourceRadii[(i+2)%256]
 )/16);
 const smooth=pack.chinSmooth;
 const radii=smooth?baseRadii.map((radius,i)=>{
  const angle=i*360/256;
  const weight=THREE.MathUtils.smoothstep(angle,smooth.fadeIn[0],smooth.fadeIn[1])*
   (1-THREE.MathUtils.smoothstep(angle,smooth.fadeOut[0],smooth.fadeOut[1]));
  if(weight===0)return radius;
  let rounded=0;
  for(let d=-smooth.radius;d<=smooth.radius;d++)rounded+=baseRadii[(i+d+256)%256]*(smooth.radius+1-Math.abs(d));
  const denom=(smooth.radius+1)*(smooth.radius+1);
  return THREE.MathUtils.lerp(radius,rounded/denom,weight*smooth.mix);
 }):baseRadii;
 const borderWidth=pack.borderWidth;
 function radiusAt(sample){
  const k=Math.floor(sample),t=sample-k;
  const a=radii[(k+255)%256],b=radii[k%256],c=radii[(k+1)%256],d=radii[(k+2)%256];
  return .21*(b+.5*t*(c-a+t*(2*a-5*b+4*c-d+t*(3*b-a-3*c+d))))+borderWidth;
 }
 const cleanFront=front;
 const edgeColor=new THREE.Color(pack.rim);
 const [leftEye,rightEye]=pack.eyes;
 const tilt=pack.tiltRad,cosT=Math.cos(tilt),sinT=Math.sin(tilt);
 let meshes=[],headDepth=pack.headDepth,eyeMeshes=[],renderSize=0;
 const surfaceZ=(x,y)=>{const dx=x-50,dy=y-50,a=(Math.atan2(dy,dx)+Math.PI*2)%(Math.PI*2),f=a/(Math.PI*2)*256,q=Math.hypot(dx,dy)/radiusAt(f);return headDepth*Math.sqrt(Math.max(0,1-q*q));};
 function buildEyes(){
  for(const e of eyeMeshes){group.remove(e.mesh);e.mesh.geometry.dispose();e.mesh.material.dispose();e.texture.dispose();}eyeMeshes=[];
  for(let eye=0;eye<2;eye++){
   const canvas=document.createElement('canvas');canvas.width=512;canvas.height=512;const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.generateMipmaps=false;texture.minFilter=THREE.LinearFilter;
   const positions=[],uv=[],indices=[],N=48,M=64,anchor=pack.eyes[eye],extent=pack.eyeExtent;
   for(let j=0;j<=M;j++)for(let i=0;i<=N;i++){
    const dx=(i/N-.5)*extent,dy=(j/M-.5)*extent,x=anchor.x+dx*Math.cos(tilt)-dy*Math.sin(tilt),y=anchor.y+dx*Math.sin(tilt)+dy*Math.cos(tilt);
    positions.push(x-50,50-y,surfaceZ(x,y)+.10);uv.push(i/N,1-j/M);
    if(i<N&&j<M){const k=j*(N+1)+i;indices.push(k,k+N+1,k+1,k+1,k+N+1,k+N+2);}
   }
   const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(indices);
   const mesh=new THREE.Mesh(g,new THREE.MeshBasicMaterial({map:texture,transparent:true,depthTest:false,depthWrite:false,side:THREE.FrontSide}));mesh.renderOrder=1;group.add(mesh);eyeMeshes.push({mesh,texture,canvas,key:''});
  }
 }
 function rebuild(depth){
  for(const m of meshes){group.remove(m);m.geometry.dispose();m.material.dispose();}meshes=[];
  const N=512,R=120;headDepth=pack.headDepth*depth/8;
  const positions=[],uv=[],indices=[],seams=[];
  const stride=N+1;
  const frontRim=R*stride;
  for(const sign of [1,-1]){
   const offset=positions.length/3;
   const vertex=(row,col)=>row===R?frontRim+col:offset+row*stride+col;
   for(let j=0;j<=(sign===1?R:R-1);j++)for(let i=0;i<=N;i++){
    const q=Math.sin(j/R*Math.PI/2),a=i/N*Math.PI*2;
    const r=radiusAt(i/N*256)*q,x=50+r*Math.cos(a),y=50+r*Math.sin(a);
    const z=sign*headDepth*Math.sqrt(Math.max(0,1-q*q));
    positions.push(x-50,50-y,z);
    uv.push((x-pack.uvOrigin)/pack.uvSize,1-(y-pack.uvOrigin)/pack.uvSize);
    seams.push(q);
   }
   for(let j=0;j<R;j++)for(let i=0;i<N;i++){
    const a=vertex(j,i),b=vertex(j+1,i),c=vertex(j,i+1),d=vertex(j+1,i+1);
    indices.push(a,b,c,c,b,d);
   }
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  geometry.setAttribute('seamBlend',new THREE.Float32BufferAttribute(seams,1));
  geometry.setIndex(indices);
   const material=new THREE.MeshBasicMaterial({map:front,side:THREE.DoubleSide});
   material.onBeforeCompile=shader=>{
    shader.uniforms.cleanFront={value:cleanFront};
    shader.uniforms.rimColor={value:edgeColor};
    shader.vertexShader='attribute float seamBlend; varying float vSeamBlend; varying float vHeadDepth;\n'+shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvSeamBlend=seamBlend;vHeadDepth=position.z;');
    shader.fragmentShader='uniform sampler2D cleanFront; uniform vec3 rimColor; varying float vSeamBlend; varying float vHeadDepth;\n'+shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
     #ifdef USE_MAP
      vec2 p=vec2(vMapUv.x,1.0-vMapUv.y)*${pack.uvSize.toFixed(4)}+${pack.uvOrigin.toFixed(4)};
      mat2 untilt=mat2(${cosT},${-sinT},${sinT},${cosT});
      vec2 leftEye=untilt*(p-vec2(${leftEye.x},${leftEye.y}))/vec2(${leftEye.rx},${leftEye.ry});
      vec2 rightEye=untilt*(p-vec2(${rightEye.x},${rightEye.y}))/vec2(${rightEye.rx},${rightEye.ry});
      if(vHeadDepth>0.0 && min(dot(leftEye,leftEye),dot(rightEye,rightEye))<1.0){
       vec2 center=dot(leftEye,leftEye)<dot(rightEye,rightEye)?vec2(${leftEye.x},${leftEye.y}):vec2(${rightEye.x},${rightEye.y});
       vec2 local=untilt*(p-center);
       vec2 tangent=vec2(${cosT},${sinT});
       vec2 offset=tangent*4.0;
       vec2 along=vec2(${-sinT},${cosT})*local.y;
       vec2 uvA=(center+along-offset-${pack.uvOrigin.toFixed(4)})/${pack.uvSize.toFixed(4)};
       vec2 uvB=(center+along+offset-${pack.uvOrigin.toFixed(4)})/${pack.uvSize.toFixed(4)};
       uvA.y=1.0-uvA.y;uvB.y=1.0-uvB.y;
       diffuseColor.rgb=mix(texture2D(cleanFront,uvA).rgb,texture2D(cleanFront,uvB).rgb,clamp((local.x+4.0)/8.0,0.0,1.0));
      }
      float rim=smoothstep(0.986,1.0,vSeamBlend);
      diffuseColor.rgb=mix(diffuseColor.rgb,rimColor,max(max(rim,step(vHeadDepth,0.0)),1.0-diffuseColor.a));
      diffuseColor.a=1.0;
     #endif
    `);
   };
   const mesh=new THREE.Mesh(geometry,material);group.add(mesh);meshes.push(mesh);
  buildEyes();
 }
 rebuild(pack.rebuildDepth);
 return {dispose(){for(const m of meshes){m.geometry.dispose();m.material.dispose();}for(const e of eyeMeshes){e.mesh.geometry.dispose();e.mesh.material.dispose();e.texture.dispose();}front.dispose();renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove();},rebuild,texture(enabled){for(const [i,m] of meshes.slice(0,2).entries()){m.material.map=enabled&&i===0?front:null;m.material.color.set(enabled&&i===0?0xffffff:pack.rim);m.material.needsUpdate=true;}},draw(yaw,pitch,states,nativeQuat=null,dt=0,headScale=1){
  const size=host.clientWidth;
  const projectedSize=Math.max(1,size*headScale*.1474*Math.cos(yaw)*Math.cos(pitch));
  const minStroke=Math.ceil(330/projectedSize);
  states?.forEach((state,i)=>{
   const e=eyeMeshes[i],key=JSON.stringify([state,minStroke]);
   if(e.key===key)return;
   e.key=key;
   const width=Math.max(state.width,minStroke),c=e.canvas.getContext('2d');
   c.clearRect(0,0,512,512);
   c.save();
   c.translate(256,256);
   c.scale(512/220,512/220);
   c.translate(state.gazeX??0,state.gazeY??0);
   c.rotate(state.tilt*Math.PI/180);
   const closed=state.lid<=.25;
   if(!closed)c.scale(1,Math.max(state.lid,minStroke/width));
   c.strokeStyle=c.fillStyle=pack.eyePaint;
   c.lineWidth=width;
   c.lineCap=c.lineJoin='round';
   c.beginPath();
   const [firstX,firstY]=state.points[0];
   if(closed){
    const halfLength=Math.max(width*.42,minStroke);
    c.lineWidth=Math.max(minStroke,5);
    c.moveTo(-halfLength,0);
    c.lineTo(halfLength,0);
    c.stroke();
   }else if(state.points.every(([x,y])=>x===firstX&&y===firstY)){
    c.arc(firstX,firstY,width/2,0,Math.PI*2);
    c.fill();
   }else{
    c.moveTo(firstX,firstY);
    for(const [x,y] of state.points.slice(1))c.lineTo(x,y);
    c.stroke();
   }
   c.restore();
   e.texture.needsUpdate=true;
  });
  if(size!==renderSize){renderer.setSize(size,size,false);renderSize=size;}group.rotation.set(-pitch,yaw,0,'YXZ');if(nativeQuat){group.quaternion.multiply(new THREE.Quaternion(nativeQuat[1],nativeQuat[2],nativeQuat[3],nativeQuat[0]));}renderer.render(scene,camera);
 }};
}
