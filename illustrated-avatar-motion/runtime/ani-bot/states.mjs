export const stateLabels={
 idle:'待机',listening:'聆听',thinking:'思考',streaming:'输出',searching:'搜索',reading:'阅读',working:'工作',coding:'编程',running:'运行',computing:'计算',controlling:'操控',waiting:'等待',blocked:'受阻',finished:'完成',failed:'失败',sleeping:'睡着',waking:'醒来',
 happy:'开心',excited:'兴奋',laughing:'大笑',proud:'得意',curious:'好奇',playful:'顽皮',shy:'害羞',surprised:'惊讶',suspicious:'怀疑',angry:'生气',confused:'困惑',sad:'难过',drowsy:'困倦',bored:'无聊',scared:'害怕',celebrate:'庆祝',approving:'赞同',
 orbit:'环绕',radar:'雷达',progress:'进度',spawning:'聚拢',loading:'加载',dictating:'听写',sending:'发送',receiving:'接收',uploading:'上传',writing:'书写',alerting:'提醒',bouncing:'弹跳','powering-down':'关机',
 humming:'哼唱',notifying:'通知',dragging:'拖动',logo:'标志动作',showcase:'展示',turntable:'旋转展示'
};
export const groupLabels={Lifecycle:'任务状态',Reactions:'情绪反应',Morphs:'形态变化',Product:'交互动作',Brand:'展示动作'};

// Original engine eye centerlines are normalized in a Y-up coordinate system.
// Neutral eye centerline + rounded stroke reproduces the original 73 × 160px pill.
export function eyeStroke(eye){
 const points=eye?.pts??[[0,-.155],[0,.155]];
 const width=Math.max(1,(eye?.wid??.13)/.13*73),lid=Math.max(.025,Math.min(1.3,eye?.lidY??1));
 const xs=points.map(p=>p[0]*280),ys=points.map(p=>p[1]*280);
 // Keep neutral eyes unchanged; constrain expressive eyes to the face's proportions.
 // Scale centerline and stroke together, so wide expressions no longer become black bars.
 const spanX=Math.max(...xs)-Math.min(...xs),spanY=Math.max(...ys)-Math.min(...ys);
 const roundness=1-Math.min(1,Math.hypot(spanX,spanY)/45);
 const fit=1/Math.max(1,(spanX+width)/(110+4*roundness),(spanY+width)*lid/179);
 const mapped=points.map(([x,y])=>[x*280*fit,-y*280*fit]);
 const path=eyePath(mapped);
 return {path,points:mapped,width:width*fit,lid,tilt:-(eye?.tilt??0)*180/Math.PI};
}

function eyePath(points){return points.map(([x,y],i)=>`${i?'L':'M'}${x.toFixed(3)} ${y.toFixed(3)}`).join('');}

// Only soften the skin's eye geometry/size adaptation. Native eyelid timing stays direct.
export function smoothEye(previous,target,dt,instant=false){
 if(!previous||instant||target.lid<.98||previous.lid<.98||previous.points.length!==target.points.length)return target;
 const alpha=1-Math.exp(-Math.max(0,dt)/.035);
 const points=target.points.map((point,i)=>point.map((v,axis)=>previous.points[i][axis]+(v-previous.points[i][axis])*alpha));
 return {...target,points,path:eyePath(points),width:previous.width+(target.width-previous.width)*alpha,tilt:previous.tilt+(target.tilt-previous.tilt)*alpha};
}
