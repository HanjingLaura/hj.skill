// Same 400-unit sphere projection used by the gray avatar renderer.
// Its idle diameter is 240 units (zoom 0.6).
export function bodyMotion(frame){
 const zoom=frame.zoom??.6;
 const [sx,sy]=frame.squash??[1,1];
 const [x,y]=frame.offset??[0,0];
 return {
  x:x*zoom*50,
  y:-(y+(frame.squashAnchor??0)*(1-sy))*zoom*50,
  sx:zoom/.6*sx,
  sy:zoom/.6*sy,
 };
}
