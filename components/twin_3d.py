from __future__ import annotations

import json
from typing import Any

import streamlit.components.v1 as components


THREE_JS_URL = "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.min.js"


def _json_for_script(value: Any) -> str:
    # Avoid accidentally terminating the embedding script if app-owned text ever
    # contains a closing script tag.
    return json.dumps(value, ensure_ascii=False, default=str).replace("</", "<\\/")


def _html(payload: dict) -> str:
    data = _json_for_script(payload)
    three_url = THREE_JS_URL
    return f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<script src="{three_url}"></script>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#07111f; color:#e5edf7; }}
  #root {{ position:relative; width:100%; height:100%; min-height:650px; overflow:hidden; border-radius:24px; border:1px solid rgba(125,211,252,.15); box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 26px 70px rgba(2,6,23,.26); background:
      radial-gradient(circle at 12% 8%, rgba(37,99,235,.34), transparent 30%),
      radial-gradient(circle at 88% 78%, rgba(13,148,136,.28), transparent 32%),
      radial-gradient(circle at 50% 44%, rgba(14,116,144,.10), transparent 42%),
      linear-gradient(145deg,#050e1a 0%,#071a2d 46%,#072a34 112%); }}
  #root:before {{ content:""; position:absolute; inset:0; pointer-events:none; opacity:.15; background-image:linear-gradient(rgba(148,163,184,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(148,163,184,.10) 1px,transparent 1px); background-size:34px 34px; mask-image:linear-gradient(to bottom,transparent 0%,black 26%,black 88%,transparent 100%); }}
  #root:after {{ content:"RESEARCH DIGITAL TWIN · SECUREMESSENGER"; position:absolute; right:22px; bottom:16px; color:rgba(148,163,184,.24); font-size:8px; letter-spacing:.19em; font-weight:850; pointer-events:none; }}
  .aurora {{ position:absolute; inset:-20%; pointer-events:none; opacity:.42; filter:blur(45px); background:conic-gradient(from 180deg at 50% 50%,transparent,rgba(37,99,235,.12),transparent,rgba(20,184,166,.11),transparent); animation:auroraSpin 22s linear infinite; }}
  @keyframes auroraSpin {{ to {{ transform:rotate(360deg); }} }}
  .scanline {{ position:absolute; left:0;right:0;height:1px; top:-3%; pointer-events:none; opacity:.28; background:linear-gradient(90deg,transparent,rgba(125,211,252,.55),transparent); box-shadow:0 0 18px rgba(56,189,248,.35); animation:scan 8s linear infinite; }}
  @keyframes scan {{ to {{ top:103%; }} }}
  #scene {{ position:absolute; inset:0; }}
  canvas {{ display:block; width:100%; height:100%; }}
  .glass {{ background:linear-gradient(145deg,rgba(6,16,30,.82),rgba(9,28,44,.72)); border:1px solid rgba(148,163,184,.20); box-shadow:0 18px 44px rgba(2,6,23,.30),inset 0 1px 0 rgba(255,255,255,.025); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); }}
  .topbar {{ position:absolute; left:20px; right:20px; top:18px; display:flex; align-items:flex-start; justify-content:space-between; gap:12px; pointer-events:none; z-index:5; }}
  .titlebox {{ max-width:min(650px,67%); padding:14px 16px 13px; border-radius:16px; border-color:rgba(125,211,252,.20); }}
  .eyebrow {{ display:inline-flex; align-items:center; width:fit-content; color:#bfdbfe; background:rgba(37,99,235,.12); border:1px solid rgba(96,165,250,.20); border-radius:999px; padding:4px 7px; font-size:9px; text-transform:uppercase; letter-spacing:.13em; font-weight:850; }}
  .title {{ margin-top:8px; font-size:20px; font-weight:780; letter-spacing:-.035em; color:#f8fafc; text-shadow:0 8px 28px rgba(2,6,23,.35); }}
  .message {{ margin-top:5px; color:#aebdce; font-size:10.5px; line-height:1.5; max-width:540px; }}
  .badges {{ display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; }}
  .badge {{ padding:6px 9px; border-radius:999px; font-size:8.5px; font-weight:850; letter-spacing:.06em; text-transform:uppercase; color:#dbeafe; border:1px solid rgba(147,197,253,.26); background:linear-gradient(135deg,rgba(30,64,175,.32),rgba(15,118,110,.20)); box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 8px 20px rgba(2,6,23,.12); }}
  .operations {{ position:absolute; top:126px; left:20px; display:flex; gap:8px; max-width:74%; pointer-events:none; z-index:5; }}
  .op {{ width:124px; min-height:56px; padding:8px 10px; border-radius:12px; border:1px solid rgba(148,163,184,.17); background:linear-gradient(145deg,rgba(15,23,42,.72),rgba(10,30,44,.62)); box-shadow:0 8px 22px rgba(2,6,23,.12); }}
  .op .oid {{ font-size:9px; font-weight:850; letter-spacing:.08em; color:#7f8ea3; }}
  .op .oname {{ font-size:11px; font-weight:760; margin-top:2px; color:#b8c5d4; }}
  .op .osub {{ font-size:8.5px; margin-top:1px; color:#64748b; }}
  .op.complete {{ border-color:rgba(52,211,153,.34); background:rgba(6,78,59,.28); }}
  .op.complete .oid,.op.complete .oname {{ color:#6ee7b7; }}
  .op.active {{ border-color:rgba(96,165,250,.68); background:rgba(30,64,175,.37); box-shadow:0 0 0 1px rgba(96,165,250,.16),0 0 28px rgba(37,99,235,.16); }}
  .op.active .oid,.op.active .oname {{ color:#bfdbfe; }}
  .legend {{ position:absolute; left:20px; bottom:22px; display:flex; flex-wrap:wrap; gap:9px; padding:8px 11px; border-radius:12px; pointer-events:none; z-index:6; }}
  .legend span {{ display:inline-flex; align-items:center; gap:5px; font-size:9px; color:#94a3b8; }}
  .dot {{ width:7px; height:7px; border-radius:50%; display:inline-block; box-shadow:0 0 8px currentColor; }}
  .toolbar {{ position:absolute; right:20px; top:126px; display:flex; flex-direction:column; gap:7px; z-index:6; }}
  .toolbar button {{ appearance:none; border:1px solid rgba(148,163,184,.20); background:linear-gradient(145deg,rgba(7,17,31,.82),rgba(15,37,55,.72)); color:#d6e1ee; border-radius:10px; height:35px; min-width:84px; padding:0 10px; font-size:9.5px; font-weight:780; cursor:pointer; backdrop-filter:blur(10px); box-shadow:0 8px 22px rgba(2,6,23,.13); }}
  .toolbar button:hover {{ border-color:rgba(96,165,250,.62); color:white; background:linear-gradient(145deg,rgba(16,36,61,.94),rgba(17,52,72,.88)); transform:translateX(-2px); }}
  .toolbar button.active {{ border-color:rgba(52,211,153,.58); color:#a7f3d0; background:rgba(6,78,59,.38); }}
  .detail {{ position:absolute; right:20px; bottom:28px; width:270px; padding:13px 14px; border-radius:14px; opacity:0; transform:translateY(8px); transition:.18s ease; pointer-events:none; z-index:7; }}
  .detail.show {{ opacity:1; transform:translateY(0); }}
  .detail .dname {{ font-size:13px; font-weight:790; color:#f8fafc; }}
  .detail .dmeta {{ margin-top:3px; font-size:9px; color:#7dd3fc; text-transform:uppercase; letter-spacing:.07em; font-weight:800; }}
  .detail .ddesc {{ margin-top:7px; font-size:10px; line-height:1.45; color:#a8b5c5; }}
  .detail .dstatus {{ display:inline-flex; margin-top:8px; border-radius:999px; padding:4px 7px; font-size:9px; font-weight:800; background:rgba(148,163,184,.12); border:1px solid rgba(148,163,184,.2); }}
  .hudrail {{ position:absolute; left:50%; top:22px; transform:translateX(-50%); display:flex; align-items:center; gap:7px; z-index:5; pointer-events:none; }}
  .huditem {{ display:flex;align-items:center;gap:5px;padding:5px 8px;border-radius:999px;border:1px solid rgba(148,163,184,.14);background:rgba(4,14,26,.48);color:#8fa2b8;font-size:8px;font-weight:750;letter-spacing:.035em;backdrop-filter:blur(9px); }}
  .hudpulse {{ width:6px;height:6px;border-radius:50%;background:#34d399;box-shadow:0 0 10px rgba(52,211,153,.7); }}
  .player {{ position:absolute; left:50%; bottom:20px; transform:translateX(-50%); width:min(720px,calc(100% - 630px)); min-width:420px; padding:10px 12px; border-radius:14px; display:none; z-index:8; }}
  .player.show {{ display:block; }}
  .p-row {{ display:flex; align-items:center; gap:8px; }}
  .play {{ width:34px; height:30px; border:1px solid rgba(96,165,250,.35); border-radius:9px; color:#dbeafe; background:rgba(30,64,175,.35); cursor:pointer; font-size:12px; }}
  .speed {{ height:28px; min-width:36px; border-radius:8px; border:1px solid rgba(148,163,184,.2); background:rgba(15,23,42,.7); color:#94a3b8; font-size:9px; font-weight:800; cursor:pointer; }}
  .speed.active {{ color:white; border-color:#60a5fa; background:rgba(37,99,235,.42); }}
  #seek {{ flex:1; accent-color:#60a5fa; min-width:120px; }}
  .counter {{ min-width:56px; text-align:right; font-size:9px; color:#94a3b8; }}
  .source {{ margin-top:5px; display:flex; justify-content:space-between; gap:12px; color:#64748b; font-size:8.5px; }}
  .source strong {{ color:#94a3b8; font-weight:700; }}
  .error {{ position:absolute; inset:25% 12%; display:none; align-items:center; justify-content:center; text-align:center; border-radius:16px; padding:24px; color:#cbd5e1; }}
  @media(max-width:900px) {{
    .operations {{ max-width:calc(100% - 36px); right:18px; overflow:auto; }}
    .op {{ min-width:100px; }}
    .detail {{ display:none; }}
    .player {{ width:calc(100% - 36px); min-width:0; bottom:16px; }}
    .legend {{ display:none; }}
    .titlebox {{ max-width:72%; }}
  }}
</style>
</head>
<body>
<div id="root">
  <div class="aurora"></div>
  <div class="scanline"></div>
  <div id="scene"></div>
  <div class="hudrail">
    <div class="huditem"><i class="hudpulse"></i>STATE LINKED</div>
    <div class="huditem" id="activeHud">NO ACTIVE RISK</div>
  </div>
  <div class="topbar">
    <div class="titlebox glass">
      <div class="eyebrow" id="eyebrow">Interactive Digital Twin</div>
      <div class="title" id="frameTitle">Loading Digital Twin…</div>
      <div class="message" id="frameMessage">Preparing governed state visualization.</div>
    </div>
    <div class="badges">
      <div class="badge" id="phaseBadge">READY</div>
      <div class="badge" id="versionBadge">Twin</div>
    </div>
  </div>
  <div class="operations" id="operations"></div>
  <div class="toolbar">
    <button id="rotateBtn">Auto-rotate</button>
    <button id="focusBtn">Focus active</button>
    <button id="resetCameraBtn">Fit scene</button>
  </div>
  <div class="detail glass" id="detail">
    <div class="dname" id="dname"></div>
    <div class="dmeta" id="dmeta"></div>
    <div class="ddesc" id="ddesc"></div>
    <div class="dstatus" id="dstatus"></div>
  </div>
  <div class="legend glass">
    <span><i class="dot" style="color:#34d399;background:#34d399"></i>Healthy</span>
    <span><i class="dot" style="color:#f59e0b;background:#f59e0b"></i>Testing</span>
    <span><i class="dot" style="color:#ef4444;background:#ef4444"></i>Vulnerable</span>
    <span><i class="dot" style="color:#22c55e;background:#22c55e"></i>Secured</span>
  </div>
  <div class="player glass" id="player">
    <div class="p-row">
      <button class="play" id="playBtn">▶</button>
      <input id="seek" type="range" min="0" max="0" value="0" step="1" />
      <button class="speed active" data-speed="1">1×</button>
      <button class="speed" data-speed="3">3×</button>
      <button class="speed" data-speed="5">5×</button>
      <div class="counter" id="counter">1 / 1</div>
    </div>
    <div class="source"><span id="sourceText"></span><strong id="timeText"></strong></div>
  </div>
  <div class="error glass" id="errorBox">
    <div><strong>3D renderer unavailable.</strong><br/>Use the 2D fallback tab. The Three.js library could not be loaded in this browser/network.</div>
  </div>
</div>
<script>
const PAYLOAD = {data};
const frames = PAYLOAD.frames || [];
const mode = PAYLOAD.mode || 'live';
const root = document.getElementById('root');
const sceneHost = document.getElementById('scene');
const errorBox = document.getElementById('errorBox');

if (!window.THREE) {{
  errorBox.style.display = 'flex';
  throw new Error('Three.js failed to load');
}}

const STATUS = {{
  healthy:    {{ color:0x34d399, emissive:0x063d2c }},
  testing:    {{ color:0xf59e0b, emissive:0x5b3203 }},
  vulnerable: {{ color:0xef4444, emissive:0x631515 }},
  secured:    {{ color:0x22c55e, emissive:0x07592b }},
  unknown:    {{ color:0x60a5fa, emissive:0x102a54 }}
}};
const OP_COLOR = {{O1:0x60a5fa,O2:0xf59e0b,O3:0xa78bfa,O4:0x34d399}};

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x06101d, 0.026);
const camera = new THREE.PerspectiveCamera(39, 1, 0.1, 100);
camera.position.set(0, 1.45, 18.0);
const renderer = new THREE.WebGLRenderer({{antialias:true,alpha:true}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x000000,0);
sceneHost.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xb9d8ff, 1.12));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.35);
keyLight.position.set(7,10,9); scene.add(keyLight);
const rimLight = new THREE.PointLight(0x38bdf8, 20, 28); rimLight.position.set(-6,3,7); scene.add(rimLight);
const greenLight = new THREE.PointLight(0x2dd4bf, 14, 24); greenLight.position.set(6,-1.5,4); scene.add(greenLight);
const blueFill = new THREE.PointLight(0x2563eb, 9, 20); blueFill.position.set(0,5,-5); scene.add(blueFill);
const activeLight = new THREE.PointLight(0x60a5fa, 0, 7); scene.add(activeLight);

const grid = new THREE.GridHelper(26, 26, 0x315274, 0x152a40);
grid.position.y = -4.45; grid.material.opacity=.25; grid.material.transparent=true; scene.add(grid);
const floor = new THREE.Mesh(new THREE.CircleGeometry(11.2,80),new THREE.MeshBasicMaterial({{color:0x071827,transparent:true,opacity:.36,depthWrite:false}}));
floor.rotation.x=-Math.PI/2; floor.position.y=-4.47; scene.add(floor);
const orbitRingA = new THREE.Mesh(new THREE.RingGeometry(6.4,6.43,96),new THREE.MeshBasicMaterial({{color:0x2563eb,transparent:true,opacity:.18,side:THREE.DoubleSide,depthWrite:false}}));
orbitRingA.rotation.x=-Math.PI/2; orbitRingA.position.y=-4.43; scene.add(orbitRingA);
const orbitRingB = new THREE.Mesh(new THREE.RingGeometry(8.2,8.23,96),new THREE.MeshBasicMaterial({{color:0x14b8a6,transparent:true,opacity:.13,side:THREE.DoubleSide,depthWrite:false}}));
orbitRingB.rotation.x=-Math.PI/2; orbitRingB.position.y=-4.42; scene.add(orbitRingB);

const starGeo = new THREE.BufferGeometry();
const starPositions = [];
for(let i=0;i<240;i++) starPositions.push((Math.random()-.5)*30, (Math.random()-.35)*19, (Math.random()-.5)*18);
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPositions,3));
const stars = new THREE.Points(starGeo,new THREE.PointsMaterial({{color:0x7fa5c8,size:.028,transparent:true,opacity:.48}}));
scene.add(stars);

const twinGroup = new THREE.Group();
scene.add(twinGroup);
twinGroup.rotation.x=-.035;
let nodeMeshes = new Map();
let edgeObjects = [];
let pulseParticles = [];
let currentFrame = null;
let autoRotate = false;
let selectedMesh = null;

const fixedPositions = {{
  client:[0,3.65,0.55], gateway:[0,1.60,0.20], auth:[-5.55,-0.25,-0.10],
  message:[0,-0.52,0.80], data_export:[5.55,-0.25,-0.10],
  integration:[-4.75,-2.58,-1.65], legal:[-1.62,-2.86,-2.20],
  bot_mgmt:[1.62,-2.86,-2.20], feature:[4.75,-2.58,-1.60], database:[0,-3.62,1.20]
}};

function escapeText(s) {{ return String(s ?? ''); }}
function colorFor(status) {{ return STATUS[status] || STATUS.unknown; }}

function makeLabel(component) {{
  const canvas=document.createElement('canvas'); canvas.width=512; canvas.height=154;
  const ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='rgba(4,12,24,.91)'; roundRect(ctx,18,18,476,118,18); ctx.fill();
  ctx.strokeStyle='rgba(125,211,252,.22)'; ctx.lineWidth=2; roundRect(ctx,18,18,476,118,18); ctx.stroke();
  ctx.fillStyle='#f8fafc'; ctx.font='700 31px Inter,Arial,sans-serif'; ctx.textAlign='center';
  let name=escapeText(component.name); if(name.length>26) name=name.slice(0,25)+'…'; ctx.fillText(name,256,64);
  const c=colorFor(component.status); ctx.fillStyle='#9fb0c2'; ctx.font='700 20px Inter,Arial,sans-serif';
  ctx.fillText(escapeText(component.status || 'unknown').toUpperCase(),256,103);
  const texture=new THREE.CanvasTexture(canvas); texture.colorSpace=THREE.SRGBColorSpace; texture.needsUpdate=true;
  const material=new THREE.SpriteMaterial({{map:texture,transparent:true,depthTest:false}});
  const sprite=new THREE.Sprite(material); sprite.scale.set(2.92,.92,1); sprite.position.y=1.08; sprite.renderOrder=10; return sprite;
}}
function roundRect(ctx,x,y,w,h,r) {{
  ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
}}

function geometryFor(component) {{
  if(component.kind==='client') return new THREE.SphereGeometry(.60,36,24);
  if(component.kind==='database') return new THREE.CylinderGeometry(.74,.74,1.08,36);
  if(component.id==='gateway') return new THREE.OctahedronGeometry(.74,0);
  if(component.id==='auth') return new THREE.DodecahedronGeometry(.66,0);
  if(component.id==='data_export') return new THREE.CylinderGeometry(.66,.78,.90,6);
  if(component.id==='legal') return new THREE.IcosahedronGeometry(.65,0);
  if(component.id==='bot_mgmt') return new THREE.OctahedronGeometry(.66,1);
  if(component.id==='integration') return new THREE.BoxGeometry(1.30,.78,.86,3,2,2);
  if(component.id==='feature') return new THREE.BoxGeometry(1.30,.78,.86,3,2,2);
  return new THREE.BoxGeometry(1.34,.84,.88,3,2,2);
}}

function createNode(id, component, index, count) {{
  component.id=id;
  let pos=fixedPositions[id];
  if(!pos) {{ const a=(index/Math.max(count,1))*Math.PI*2; pos=[Math.cos(a)*4,Math.sin(a)*2,Math.sin(a*.7)*1.2]; }}
  const palette=colorFor(component.status);
  const material=new THREE.MeshStandardMaterial({{
    color:palette.color, emissive:palette.emissive, emissiveIntensity:component.status==='vulnerable'?1.15:.68,
    roughness:.25, metalness:.28, transparent:true, opacity:.97
  }});
  const mesh=new THREE.Mesh(geometryFor(component),material); mesh.position.set(...pos); mesh.userData={{id,component}};
  const edge=new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry),new THREE.LineBasicMaterial({{color:0xdbeafe,transparent:true,opacity:.24}}));
  mesh.add(edge); mesh.add(makeLabel(component));
  const halo=new THREE.Mesh(new THREE.SphereGeometry(.9,24,18),new THREE.MeshBasicMaterial({{color:palette.color,transparent:true,opacity:.065,depthWrite:false}}));
  halo.scale.set(1.35,1.35,1.35); halo.userData.halo=true; mesh.add(halo);
  const baseRing=new THREE.Mesh(new THREE.RingGeometry(.74,1.10,56),new THREE.MeshBasicMaterial({{color:palette.color,transparent:true,opacity:.23,side:THREE.DoubleSide,depthWrite:false}}));
  baseRing.rotation.x=-Math.PI/2; baseRing.position.y=-.76; baseRing.userData.baseRing=true; mesh.add(baseRing);
  const pedestal=new THREE.Mesh(new THREE.CylinderGeometry(.82,.98,.10,40),new THREE.MeshStandardMaterial({{color:0x102638,emissive:palette.emissive,emissiveIntensity:.28,roughness:.46,metalness:.42,transparent:true,opacity:.82}}));
  pedestal.position.y=-.72; pedestal.userData.pedestal=true; mesh.add(pedestal);
  const beam=new THREE.Mesh(new THREE.CylinderGeometry(.025,.025,Math.max(.8,pos[1]+4.40),10),new THREE.MeshBasicMaterial({{color:palette.color,transparent:true,opacity:.08,depthWrite:false}}));
  beam.position.y=-(Math.max(.8,pos[1]+4.40))/2-.75; beam.userData.beam=true; mesh.add(beam);
  twinGroup.add(mesh); nodeMeshes.set(id,mesh); return mesh;
}}

function createEdge(source,target) {{
  const a=nodeMeshes.get(source), b=nodeMeshes.get(target); if(!a||!b) return;
  const start=a.position.clone(), end=b.position.clone();
  const mid=start.clone().lerp(end,.5);
  mid.z += Math.min(1.15, start.distanceTo(end)*.10);
  mid.y += .12;
  const curve=new THREE.QuadraticBezierCurve3(start,mid,end);
  const points=curve.getPoints(28);
  const geo=new THREE.BufferGeometry().setFromPoints(points);
  const line=new THREE.Line(geo,new THREE.LineBasicMaterial({{color:0x557aa1,transparent:true,opacity:.52}}));
  line.userData={{source,target,curve,glow:false}}; twinGroup.add(line); edgeObjects.push(line);
  const glow=new THREE.Line(geo.clone(),new THREE.LineBasicMaterial({{color:0x60a5fa,transparent:true,opacity:.10}}));
  glow.userData={{source,target,curve,glow:true}}; glow.scale.setScalar(1.002); twinGroup.add(glow); edgeObjects.push(glow);
  for(let i=0;i<2;i++) {{
    const p=new THREE.Mesh(new THREE.SphereGeometry(.062,14,10),new THREE.MeshBasicMaterial({{color:0x60a5fa,transparent:true,opacity:.0}}));
    p.userData={{source,target,t:(Math.random()+i*.5)%1,curve,offset:i*.48}}; twinGroup.add(p); pulseParticles.push(p);
  }}
}}

function rebuildTwin(frame) {{
  while(twinGroup.children.length) twinGroup.remove(twinGroup.children[0]);
  nodeMeshes=new Map(); edgeObjects=[]; pulseParticles=[];
  const twin=frame.twin || {{components:{{}},edges:[]}};
  const entries=Object.entries(twin.components || {{}});
  entries.forEach(([id,c],i)=>createNode(id,{{...c}},i,entries.length));
  (twin.edges || []).forEach(e=>createEdge(e[0],e[1]));
  applyFrameHighlights(frame);
}}

function applyFrameHighlights(frame) {{
  const active=frame.active_component;
  nodeMeshes.forEach((mesh,id)=>{{
    const component=mesh.userData.component;
    const palette=colorFor(component.status);
    mesh.material.color.setHex(palette.color); mesh.material.emissive.setHex(palette.emissive);
    mesh.material.emissiveIntensity=(id===active?1.45:(component.status==='vulnerable'?1.15:.68));
    mesh.scale.setScalar(id===active?1.10:1);
  }});
  const opColor=OP_COLOR[frame.focus_operation] || 0x60a5fa;
  const activeMesh=active ? nodeMeshes.get(active) : null;
  if(activeMesh) {{
    activeLight.color.setHex(opColor); activeLight.intensity=15; activeLight.position.copy(activeMesh.position); activeLight.position.z+=2.4;
    document.getElementById('activeHud').textContent='ACTIVE · '+String((activeMesh.userData.component||{{}}).name||active).toUpperCase();
  }} else {{
    activeLight.intensity=0; document.getElementById('activeHud').textContent='NO ACTIVE RISK';
  }}
  pulseParticles.forEach(p=>{{
    const related=!active || p.userData.source===active || p.userData.target===active;
    p.material.color.setHex(opColor); p.material.opacity=related?.95:.08;
  }});
  edgeObjects.forEach(line=>{{
    const related=!active || line.userData.source===active || line.userData.target===active;
    line.material.color.setHex(related?opColor:0x4f7195);
    line.material.opacity=related?(line.userData.glow?.18:.76):(line.userData.glow?.035:.20);
  }});
}}

function renderOperations(ops) {{
  const host=document.getElementById('operations'); host.innerHTML='';
  (ops||[]).forEach(op=>{{
    const el=document.createElement('div'); el.className='op '+(op.status||'pending');
    el.innerHTML=`<div class="oid">${{op.id}} · ${{op.status==='complete'?'DONE':op.status==='active'?'ACTIVE':'WAIT'}}</div><div class="oname">${{escapeText(op.name)}}</div><div class="osub">${{escapeText(op.subtitle)}}</div>`;
    host.appendChild(el);
  }});
}}

function setFrame(index) {{
  if(!frames.length) return;
  currentIndex=Math.max(0,Math.min(index,frames.length-1)); currentFrame=frames[currentIndex];
  rebuildTwin(currentFrame); renderOperations(currentFrame.operations);
  document.getElementById('frameTitle').textContent=currentFrame.title || 'Digital Twin state';
  document.getElementById('frameMessage').textContent=currentFrame.message || '';
  document.getElementById('phaseBadge').textContent=String(currentFrame.phase||'ready').replaceAll('_',' ').toUpperCase();
  document.getElementById('versionBadge').textContent='TWIN v'+String((currentFrame.twin||{{}}).version||'—');
  document.getElementById('counter').textContent=`${{currentIndex+1}} / ${{frames.length}}`;
  document.getElementById('seek').value=String(currentIndex);
  document.getElementById('timeText').textContent=currentFrame.created_at ? new Date(currentFrame.created_at).toLocaleTimeString() : '';
  document.getElementById('sourceText').textContent=(PAYLOAD.source_label||'Live state') + (currentFrame.state_hash ? ' · integrity-backed snapshot' : '');
  hideDetail();
}}

function showDetail(mesh) {{
  if(!mesh) return hideDetail();
  selectedMesh=mesh; const c=mesh.userData.component||{{}};
  document.getElementById('dname').textContent=c.name||mesh.userData.id;
  document.getElementById('dmeta').textContent=(c.kind||'component')+' · v'+(c.version||'—');
  document.getElementById('ddesc').textContent=c.description||'Digital Twin component';
  const s=document.getElementById('dstatus'); s.textContent=String(c.status||'unknown').toUpperCase();
  document.getElementById('detail').classList.add('show');
}}
function hideDetail() {{ selectedMesh=null; document.getElementById('detail').classList.remove('show'); }}

let width=1,height=1;
function resize() {{
  const r=root.getBoundingClientRect(); width=Math.max(1,r.width); height=Math.max(1,r.height);
  renderer.setSize(width,height,false); camera.aspect=width/height; camera.updateProjectionMatrix();
}}
new ResizeObserver(resize).observe(root); resize();

let dragging=false,lastX=0,lastY=0,moved=false;
renderer.domElement.addEventListener('pointerdown',e=>{{dragging=true;lastX=e.clientX;lastY=e.clientY;moved=false;renderer.domElement.setPointerCapture(e.pointerId);}});
renderer.domElement.addEventListener('pointermove',e=>{{
  if(!dragging) return; const dx=e.clientX-lastX,dy=e.clientY-lastY; if(Math.abs(dx)+Math.abs(dy)>2)moved=true;
  twinGroup.rotation.y+=dx*.006; twinGroup.rotation.x=Math.max(-.45,Math.min(.45,twinGroup.rotation.x+dy*.004)); lastX=e.clientX;lastY=e.clientY;
}});
renderer.domElement.addEventListener('pointerup',e=>{{dragging=false;if(!moved)pick(e);}});
renderer.domElement.addEventListener('pointermove',e=>{{
  if(dragging) return; const r=renderer.domElement.getBoundingClientRect(); pointer.x=((e.clientX-r.left)/r.width)*2-1; pointer.y=-((e.clientY-r.top)/r.height)*2+1;
  raycaster.setFromCamera(pointer,camera); const hits=raycaster.intersectObjects([...nodeMeshes.values()],false); renderer.domElement.style.cursor=hits.length?'pointer':'grab';
}});
renderer.domElement.addEventListener('wheel',e=>{{e.preventDefault();camera.position.z=Math.max(8,Math.min(24,camera.position.z+e.deltaY*.012));}},{{passive:false}});

const raycaster=new THREE.Raycaster(); const pointer=new THREE.Vector2();
function pick(e) {{
  const r=renderer.domElement.getBoundingClientRect(); pointer.x=((e.clientX-r.left)/r.width)*2-1; pointer.y=-((e.clientY-r.top)/r.height)*2+1;
  raycaster.setFromCamera(pointer,camera); const hits=raycaster.intersectObjects([...nodeMeshes.values()],false); if(hits.length) showDetail(hits[0].object); else hideDetail();
}}

document.getElementById('rotateBtn').onclick=()=>{{autoRotate=!autoRotate;const b=document.getElementById('rotateBtn');b.textContent=autoRotate?'Stop rotation':'Auto-rotate';b.classList.toggle('active',autoRotate);}};
document.getElementById('focusBtn').onclick=()=>{{
  const id=(currentFrame||{{}}).active_component; const mesh=id?nodeMeshes.get(id):null;
  if(mesh) {{ showDetail(mesh); twinGroup.rotation.y=0; twinGroup.rotation.x=-.035; camera.position.set(0,1.45,15.3); }}
}};
document.getElementById('resetCameraBtn').onclick=()=>{{twinGroup.rotation.set(-.035,0,0);camera.position.set(0,1.45,18.0);hideDetail();}};

let currentIndex=0,playing=false,speed=1,timer=null;
const player=document.getElementById('player'); const seek=document.getElementById('seek'); const playBtn=document.getElementById('playBtn');
if(mode==='replay' && frames.length>1) {{ player.classList.add('show'); seek.max=String(frames.length-1); }}
function stopTimer() {{ if(timer){{clearTimeout(timer);timer=null;}} }}
function scheduleNext() {{
  stopTimer(); if(!playing) return;
  const hold=Math.max(420,Number((frames[currentIndex]||{{}}).hold_ms||2400)/speed);
  timer=setTimeout(()=>{{
    if(currentIndex>=frames.length-1){{playing=false;playBtn.textContent='▶';return;}}
    setFrame(currentIndex+1); scheduleNext();
  }},hold);
}}
playBtn.onclick=()=>{{
  if(currentIndex>=frames.length-1 && !playing) setFrame(0);
  playing=!playing; playBtn.textContent=playing?'❚❚':'▶'; scheduleNext();
}};
seek.oninput=()=>{{playing=false;playBtn.textContent='▶';stopTimer();setFrame(Number(seek.value));}};
document.querySelectorAll('.speed').forEach(btn=>btn.onclick=()=>{{
  speed=Number(btn.dataset.speed||1); document.querySelectorAll('.speed').forEach(b=>b.classList.toggle('active',b===btn)); if(playing)scheduleNext();
}});

const clock=new THREE.Clock();
function animate() {{
  requestAnimationFrame(animate); const dt=clock.getDelta(); const elapsed=clock.elapsedTime;
  if(autoRotate) twinGroup.rotation.y+=dt*.105;
  nodeMeshes.forEach((mesh,id)=>{{
    const halo=mesh.children.find(c=>c.userData&&c.userData.halo); if(halo){{const base=id===(currentFrame||{{}}).active_component?1.42:1.28; const pulse=base+Math.sin(elapsed*2.6+id.length)*.06;halo.scale.setScalar(pulse);}}
  }});
  pulseParticles.forEach(p=>{{
    p.userData.t=(p.userData.t+dt*.18)%1; p.position.copy(p.userData.curve.getPoint(p.userData.t));
    const pulse=.82+Math.sin(elapsed*5+p.userData.t*8)*.18; p.scale.setScalar(pulse);
  }});
  orbitRingA.rotation.z+=dt*.014; orbitRingB.rotation.z-=dt*.010;
  nodeMeshes.forEach((mesh,id)=>{{
    const ring=mesh.children.find(c=>c.userData&&c.userData.baseRing); if(ring) ring.rotation.z+=dt*(id===(currentFrame||{{}}).active_component ? 0.55 : 0.12);
    const beam=mesh.children.find(c=>c.userData&&c.userData.beam); if(beam) beam.material.opacity=(id===(currentFrame||{{}}).active_component ? 0.20 : 0.055)+(Math.sin(elapsed*2+id.length)+1)*.012;
  }});
  stars.rotation.y+=dt*.006; renderer.render(scene,camera);
}}

if(frames.length) setFrame(0); animate();
</script>
</body>
</html>
"""


def render_live_twin_3d(frame: dict, *, height: int = 720) -> None:
    """Render the current governed Digital Twin state in an interactive WebGL scene."""
    payload = {
        "mode": "live",
        "source_label": "Live governed Twin state",
        "frames": [frame],
    }
    components.html(_html(payload), height=height, scrolling=False)


def render_twin_replay(bundle: dict, *, height: int = 760) -> None:
    """Render an evidence-backed replay bundle with 1x/3x/5x playback controls."""
    payload = {
        "mode": "replay",
        "source_label": (
            "PostgreSQL evidence replay"
            if bundle.get("source") == "postgresql-twin-snapshots"
            else "Built-in demonstration replay"
        ),
        "frames": bundle.get("frames", []),
    }
    components.html(_html(payload), height=height, scrolling=False)
