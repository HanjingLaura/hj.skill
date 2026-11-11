import {createPrimaryPlayer} from '/runtime/ani-bot/player.js?v=3';
const host=document.querySelector('#head');
const pack=await fetch('./pack.json').then(r=>r.json());
pack.artworkUrl=new URL('./front.png?v=2',location.href).href;
const player=await createPrimaryPlayer(host,pack);
import {avatarStates as states} from '/runtime/ani-bot/catalog.js';
let state='idle',paused=false,clock=0,last=performance.now(),look=null;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
function select(value){if(!Object.hasOwn(states,value))return;state=value;document.querySelector('#state-select').value=value;document.querySelector('#status').textContent=states[value];for(const b of document.querySelectorAll('[data-state]'))b.setAttribute('aria-pressed',String(b.dataset.state===value));}
for(const [id,label] of Object.entries(states)){const b=document.createElement('button');b.textContent=label;b.dataset.state=id;b.onclick=()=>select(id);document.querySelector('#state-grid').append(b);document.querySelector('#state-select').add(new Option(label,id));}
select('idle');
let autoplay=false,autoElapsed=0;
const ids=Object.keys(states);
function advanceState(offset){select(ids[(ids.indexOf(state)+offset+ids.length)%ids.length]);autoElapsed=0;}
document.querySelector('#previous').onclick=()=>advanceState(-1);
document.querySelector('#next').onclick=()=>advanceState(1);
document.querySelector('#state-select').onchange=e=>select(e.target.value);
document.querySelector('#auto').onclick=e=>{autoplay=!autoplay;autoElapsed=0;e.target.textContent=autoplay?'停止切换':'自动切换';};

document.querySelector('#pause').onclick=e=>{paused=!paused;e.target.textContent=paused?'继续':'暂停';};
window.addEventListener('pointermove',e=>{const r=host.getBoundingClientRect();look={yaw:Math.max(-15,Math.min(15,(e.clientX-r.x-r.width/2)/r.width*30)),pitch:Math.max(-8,Math.min(8,-(e.clientY-r.y-r.height/2)/r.height*16))};});
document.documentElement.addEventListener('pointerleave',()=>look=null);
function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(!paused){clock+=dt;if(autoplay){autoElapsed+=dt;if(autoElapsed>=4)advanceState(1);}player.paint(clock,state,1,document.querySelector('#follow').checked&&!reduced.matches?look:null,reduced.matches);}requestAnimationFrame(frame);}
requestAnimationFrame(frame);
window.avatarPreview={player,select,states};
window.addEventListener('pagehide',()=>player.dispose());
