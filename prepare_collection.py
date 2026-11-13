#!/usr/bin/env python3
"""Collections premium – Centre Optique Chefchaouen.
À lancer depuis le dossier qui contient index.html et assets/ :
    pip install pillow pillow-heif
    python prepare_collection.py
Fait : 1) lit assets/images/products/livit femme + livit homme  2) regroupe les positions par modèle
3) convertit en WebP (grand + vignette + miniature)  4) remplace la section #brands de index.html
(sauvegarde : index.backup-collection.html). Relançable sans risque. Les HEIC originaux ne sont pas touchés."""
import re, json, shutil, sys
from pathlib import Path
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except ImportError:
    print("Installez d'abord : pip install pillow-heif"); sys.exit(1)

ROOT = Path(".")
SRC = {"f": ROOT/"assets/images/products/livit femme", "h": ROOT/"assets/images/products/livit homme"}
OUT = ROOT/"assets/images/products/collection"; OUT.mkdir(parents=True, exist_ok=True)
EXT = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}
PAT = re.compile(r"lunette\s*(\d+)\s*p\w*\s*(\d+)", re.I)   # accepte « postion » et « position »

# Si le dossier collection contient déjà des fichiers, on les utilise directement
USE_EXISTING = list(OUT.glob("*.webp")) and not any((SRC["f"].glob("*")) or (SRC["h"].glob("*")))

def save(im, path, size, q):
    c = im.copy(); c.thumbnail((size, size), Image.LANCZOS); c.save(path, "WEBP", quality=q, method=6)

data = []

if USE_EXISTING:
    # Parser les fichiers existants dans collection/
    print("Utilisation des fichiers WebP existants dans collection/")
    card_files = sorted(OUT.glob("*-card.webp"))
    for card in card_files:
        m = re.match(r"([fh])(\d+)-card\.webp", card.name)
        if not m:
            continue
        g, n = m.group(1), int(m.group(2))
        mid = f"{g}{n:02d}"
        # Trouver les images correspondantes
        full = sorted(OUT.glob(f"{mid}-*.webp"))
        full = [f.as_posix() for f in full if not f.name.endswith("-card.webp") and not f.name.endswith("-t.webp")]
        thumb = sorted(OUT.glob(f"{mid}-*-t.webp"))
        thumb = [f.as_posix() for f in thumb]
        data.append({"id": mid, "g": g, "n": n, "c": card.as_posix(), "i": full, "t": thumb})
else:
    # Traitement normal des fichiers source
    for g, folder in SRC.items():
        if not folder.is_dir(): print("Dossier introuvable :", folder); continue
        models = {}
        for p in sorted(folder.iterdir()):
            if p.suffix.lower() not in EXT: continue
            m = PAT.search(p.stem)
            if not m: print("Nom non reconnu (ignoré) :", p.name); continue
            models.setdefault(int(m.group(1)), {})[int(m.group(2))] = p
        for n in sorted(models):
            pos = models[n]; mid = f"{g}{n:02d}"; full, thumb = [], []
            for k in sorted(pos):
                im = ImageOps.exif_transpose(Image.open(pos[k])).convert("RGB")
                for suf, size, q, lst in (("", 1600, 82, full), ("-t", 200, 70, thumb)):
                    f = OUT/f"{mid}-{k}{suf}.webp"
                    if not f.exists(): save(im, f, size, q)
                    lst.append(f.as_posix())
                if k == min(pos):
                    f = OUT/f"{mid}-card.webp"
                    if not f.exists(): save(im, f, 720, 78)
            data.append({"id": mid, "g": g, "n": n, "c": (OUT/f"{mid}-card.webp").as_posix(), "i": full, "t": thumb})
for m in data:
    assert all(Path(x).exists() for x in [m["c"]] + m["i"] + m["t"]), m["id"]

HTML = r'''<!--COLL-S-->
<section id="brands" class="coll"><div class="w">
<div class="chead"><h2 id="ch2"></h2><p id="csub"></p></div>
<div class="chips" id="cflt" role="group"></div>
<ul id="cg" aria-live="polite"></ul>
<div hidden aria-hidden="true"><div id="bg" class="bs"></div><div id="gal" hidden><button class="btn" id="back"></button><h2 id="gt"></h2><div class="chips" id="cf"></div><div class="chips" id="sf"></div><div class="grid" id="pg"></div></div></div>
</div></section>
<div id="cmo" class="cmo" role="dialog" aria-modal="true" aria-labelledby="cmt" aria-hidden="true"><div class="cmi">
<button id="cmx" class="cmx" type="button" aria-label="Close">×</button>
<div class="cml"><div class="cms"><img id="cmi" alt="" width="1600" height="1200"><button id="cmp" class="cmn p" type="button">‹</button><button id="cmnx" class="cmn n" type="button">›</button><span id="ccnt" class="ccnt"></span></div><div id="cth" class="cth"></div></div>
<div class="cmr"><small id="cmc"></small><h3 id="cmt"></h3><a id="cmw" class="btn p" target="_blank" rel="noopener"></a></div>
</div></div>
<!--COLL-E-->'''

CSS = r'''/* COLL-CSS-START */
#brands .chead{max-width:720px;margin-bottom:8px}#brands .chead h2{max-width:none}
#csub{max-width:56ch;font-size:1.1rem;opacity:.85}
#cflt{margin:28px 0 34px}
#cg{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px;transition:opacity .25s,transform .25s}
#cg.sw{opacity:0;transform:translateY(10px)}
.cc{position:relative;display:block;width:100%;padding:10px;text-align:start;font:inherit;color:var(--navy);cursor:pointer;border-radius:22px;background:linear-gradient(145deg,rgba(255,250,243,.92),rgba(255,250,243,.55));border:1px solid rgba(20,33,61,.1);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);box-shadow:0 10px 30px rgba(20,33,61,.07);transition:transform .45s cubic-bezier(.2,.7,.2,1),box-shadow .45s}
.cc:not(.in){opacity:0;transform:translateY(28px)}
.cc.in{animation:ccIn .8s var(--d,0ms) cubic-bezier(.2,.7,.2,1) backwards}
@keyframes ccIn{from{opacity:0;transform:translateY(28px)}}
.cc:hover,.cc:focus-visible{transform:translateY(-6px);box-shadow:0 26px 54px rgba(20,33,61,.16)}
.cc:before{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:1px;background:linear-gradient(135deg,var(--coral),transparent 45%,var(--coral));-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:opacity .5s;pointer-events:none}
.cc:hover:before,.cc:focus-visible:before{opacity:.85}
.ci{display:block;aspect-ratio:4/3;border-radius:14px;overflow:hidden;background:var(--bg2)}
.ci img{display:block;width:100%;height:100%;object-fit:cover;transition:transform 1s cubic-bezier(.2,.7,.2,1)}
.cc:hover .ci img{transform:scale(1.06)}
.cb{display:block;padding:16px 8px 8px}
.cb small{display:flex;align-items:center;gap:8px;font:500 .7rem var(--sans);letter-spacing:.2em;text-transform:uppercase;color:rgba(20,33,61,.62)}
.cb small:before{content:"";width:6px;height:6px;border-radius:50%;background:var(--coral)}
[dir=rtl] .cb small{letter-spacing:0;font-family:Cairo,var(--sans}
.cb b{display:block;margin-top:6px;font:600 1.5rem/1.1 var(--serif)}[dir=rtl] .cb b{font-family:Cairo,serif;font-size:1.25rem}
.cmore{display:inline-flex;align-items:center;gap:8px;margin-top:12px;font-size:.9rem;font-weight:500;opacity:0;transform:translateY(6px);transition:opacity .4s,transform .4s}
.cmore:after{content:"→"}[dir=rtl] .cmore:after{content:"←"}
.cc:hover .cmore,.cc:focus-visible .cmore{opacity:1;transform:none}
@media(hover:none){.cmore{opacity:1;transform:none}}
@media(max-width:700px){#cg{grid-template-columns:1fr 1fr;gap:12px}.cc{padding:7px;border-radius:16px}.cb{padding:12px 4px 4px}.cb b{font-size:1.15rem}.cmore{font-size:.8rem;margin-top:8px}}
@media(max-width:360px){#cg{grid-template-columns:1fr}}
.cmo{position:fixed;inset:0;z-index:58;display:grid;place-items:center;padding:16px;background:rgba(14,24,48,.55);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);opacity:0;visibility:hidden;transition:opacity .4s,visibility .4s}
.cmo.on{opacity:1;visibility:visible}
.cmi{position:relative;display:grid;grid-template-columns:1.25fr .75fr;gap:28px;width:min(1080px,100%);max-height:calc(100svh - 32px);overflow:auto;padding:22px;border-radius:26px;color:var(--navy);background:linear-gradient(145deg,rgba(255,250,243,.97),rgba(244,237,224,.92));border:1px solid rgba(255,250,243,.6);box-shadow:0 40px 90px rgba(5,10,24,.5);transform:translateY(24px) scale(.97);transition:transform .6s cubic-bezier(.2,.7,.2,1)}
.cmo.on .cmi{transform:none}
.cms{position:relative;aspect-ratio:4/3;border-radius:16px;overflow:hidden;background:var(--bg2)}
.cms img{display:block;width:100%;height:100%;object-fit:contain;transition:opacity .25s,transform .5s}.cms img.sw{opacity:0;transform:scale(1.02)}
.cmn,.cmx{border:1px solid var(--line);background:rgba(255,250,243,.88);color:var(--navy);border-radius:50%;cursor:pointer;line-height:1;transition:background .3s,transform .3s}
.cmn{position:absolute;top:50%;translate:0 -50%;width:44px;height:44px;font-size:1.5rem}
.cmn.p{inset-inline-start:12px}.cmn.n{inset-inline-end:12px}[dir=rtl] .cmn{scale:-1 1}
.cmn:hover,.cmx:hover{background:var(--coral)}
.cmx{position:absolute;top:12px;inset-inline-end:12px;z-index:3;width:44px;height:44px;font-size:1.6rem}
.ccnt{position:absolute;bottom:10px;inset-inline-start:12px;padding:3px 10px;border-radius:20px;font-size:.78rem;background:rgba(20,33,61,.7);color:var(--cream)}
.cth{display:flex;gap:8px;margin-top:10px;overflow-x:auto;padding-bottom:4px}
.cth button{flex:none;width:72px;aspect-ratio:1;padding:0;border:2px solid transparent;border-radius:10px;overflow:hidden;cursor:pointer;background:var(--bg2);opacity:.7;transition:opacity .3s,border-color .3s}
.cth button[aria-pressed=true]{border-color:var(--coral);opacity:1}.cth img{width:100%;height:100%;object-fit:cover}
.cmr{display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:12px;padding-inline-end:36px}
.cmr small{font:500 .72rem var(--sans);letter-spacing:.22em;text-transform:uppercase;color:rgba(20,33,61,.62)}[dir=rtl] .cmr small{letter-spacing:0}
.cmr h3{font-size:clamp(2rem,4vw,2.8rem);margin-bottom:8px}
@media(max-width:820px){.cmi{grid-template-columns:1fr;gap:14px;padding:14px;border-radius:20px}.cmr{padding-inline-end:0;padding-bottom:6px}.cmr .btn{width:100%;text-align:center}}
/* COLL-CSS-END */'''

JS = r'''/* COLL-JS-START */
(()=>{
const D=__DATA__;
const CT={
fr:{t:"Nos collections exclusives",s:"Découvrez notre sélection de montures soigneusement choisies pour révéler votre style.",all:"Toutes les collections",f:"Femme",h:"Homme",m:"Lunette",d:"Découvrir le modèle",w:"Demander des informations sur WhatsApp",x:"Fermer",p:"Photo précédente",n:"Photo suivante",v:"photo",al:"Lunettes"},
en:{t:"Our exclusive collections",s:"Discover our selection of frames, carefully chosen to reveal your style.",all:"All collections",f:"Women",h:"Men",m:"Glasses",d:"Discover the model",w:"Ask for information on WhatsApp",x:"Close",p:"Previous photo",n:"Next photo",v:"photo",al:"Glasses"},
ar:{t:"مجموعاتنا الحصرية",s:"اكتشف تشكيلتنا من الإطارات المختارة بعناية لتبرز أسلوبك.",all:"كل المجموعات",f:"نساء",h:"رجال",m:"نظارة",d:"اكتشف الموديل",w:"اطلب معلومات عبر واتساب",x:"إغلاق",p:"الصورة السابقة",n:"الصورة التالية",v:"صورة",al:"نظارات"},
es:{t:"Nuestras colecciones exclusivas",s:"Descubra nuestra selección de monturas, elegidas con esmero para revelar su estilo.",all:"Todas las colecciones",f:"Mujer",h:"Hombre",m:"Gafas",d:"Descubrir el modelo",w:"Pedir información por WhatsApp",x:"Cerrar",p:"Foto anterior",n:"Foto siguiente",v:"foto",al:"Gafas"}};
const q=s=>document.querySelector(s),tx=()=>CT[L]||CT.fr,pad=n=>String(n).padStart(2,"0");
let cf="all",cur=null,ci=0,last=null;
const nm=m=>tx().m+" "+pad(m.n),cat=m=>tx()[m.g],alt=(m,i)=>`${tx().al} ${cat(m).toLowerCase()} · ${nm(m)} · ${tx().v} ${i+1}/${m.i.length}`;
const io=new IntersectionObserver(a=>a.forEach(e=>{if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target)}}),{threshold:.12,rootMargin:"0px 0px -6% 0px"});
function draw(){const t=tx();q("#cg").innerHTML=D.filter(m=>cf=="all"||m.g==cf).map((m,i)=>`<li><button type="button" class="cc" data-cid="${m.id}" style="--d:${(i%8)*70}ms" aria-label="${nm(m)} – ${cat(m)}"><span class="ci"><img src="${m.c}" alt="${alt(m,0)}" width="720" height="540" loading="lazy" decoding="async"></span><span class="cb"><small>${cat(m)}</small><b>${nm(m)}</b><span class="cmore">${t.d}</span></span></button></li>`).join("");q("#cg").querySelectorAll(".cc").forEach(e=>io.observe(e))}
function ui(){const t=tx();q("#ch2").textContent=t.t;q("#csub").textContent=t.s;
q("#cflt").innerHTML=["all","f","h"].map(k=>`<button type="button" class="chip" data-cfl="${k}" aria-pressed="${cf==k}">${k=="all"?t.all:t[k]}</button>`).join("");
q("#cmx").setAttribute("aria-label",t.x);q("#cmp").setAttribute("aria-label",t.p);q("#cmnx").setAttribute("aria-label",t.n);draw()}
function setF(k){if(k==cf)return;cf=k;q("#cflt").querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.cfl==k));const g=q("#cg");g.classList.add("sw");setTimeout(()=>{draw();g.classList.remove("sw")},matchMedia("(prefers-reduced-motion:reduce)").matches?0:220)}
function fillM(){const m=cur,x=tx();q("#cmc").textContent=cat(m);q("#cmt").textContent=nm(m);const w=q("#cmw");w.textContent=x.w;w.href=wa(T[L].wad+nm(m)+" ("+cat(m)+")");
q("#cth").innerHTML=m.t.map((s,i)=>`<button type="button" data-ct="${i}" aria-label="${x.v} ${i+1}"><img src="${s}" alt="" width="72" height="72" loading="lazy" decoding="async"></button>`).join("");
const one=m.i.length<2;q("#cmp").style.display=q("#cmnx").style.display=one?"none":"";q("#cth").style.display=one?"none":""}
function show(i,first){const m=cur,im=q("#cmi");ci=(i+m.i.length)%m.i.length;const set=()=>{im.src=m.i[ci];im.alt=alt(m,ci);im.classList.remove("sw")};
q("#cth").querySelectorAll("button").forEach((b,k)=>b.setAttribute("aria-pressed",k==ci));q("#ccnt").textContent=(ci+1)+" / "+m.i.length;
if(first){set();return}im.classList.add("sw");const p=new Image();p.onload=()=>setTimeout(set,120);p.onerror=set;p.src=m.i[ci]}
function openM(id,b){cur=D.find(m=>m.id==id);if(!cur)return;last=b;ci=0;fillM();show(0,true);const o=q("#cmo");o.classList.add("on");o.setAttribute("aria-hidden","false");document.documentElement.style.overflow="hidden";q("#cmx").focus({preventScroll:true})}
function closeM(){const o=q("#cmo");o.classList.remove("on");o.setAttribute("aria-hidden","true");document.documentElement.style.overflow="";cur=null;if(last)last.focus({preventScroll:true})}
document.addEventListener("click",e=>{const c=e.target.closest("[data-cid]");if(c)return openM(c.dataset.cid,c);const f=e.target.closest("[data-cfl]");if(f)return setF(f.dataset.cfl);
const b=e.target.closest("[data-ct]");if(b&&cur)return show(+b.dataset.ct);if(e.target.closest("#cmx")||e.target.id=="cmo")return closeM();if(e.target.closest("#cmp"))return show(ci-1);if(e.target.closest("#cmnx"))return show(ci+1)});
addEventListener("keydown",e=>{if(!cur)return;const d=document.documentElement.dir=="rtl"?-1:1;
if(e.key=="Escape"){e.stopPropagation();closeM()}else if(e.key=="ArrowRight")show(ci+d);else if(e.key=="ArrowLeft")show(ci-d);
else if(e.key=="Tab"){const f=[...q("#cmo").querySelectorAll("button,a[href]")].filter(x=>x.offsetParent);if(!f.length)return;const a=document.activeElement;if(e.shiftKey&&a==f[0]){e.preventDefault();f[f.length-1].focus()}else if(!e.shiftKey&&a==f[f.length-1]){e.preventDefault();f[0].focus()}}},true);
let sx=0;const st=q(".cms");st.addEventListener("touchstart",e=>{sx=e.touches[0].clientX},{passive:true});st.addEventListener("touchend",e=>{const d=e.changedTouches[0].clientX-sx;if(cur&&Math.abs(d)>45)show(ci+(d<0?1:-1))});
const r0=render;render=function(){r0();ui();if(cur){fillM();show(ci,true)}};
ui()})();
/* COLL-JS-END */'''

h = (ROOT/"index.html").read_text(encoding="utf-8")
shutil.copyfile("index.html", "index.backup-collection.html")
h = re.sub(r"/\* COLL-CSS-START \*/.*?/\* COLL-CSS-END \*/\n?", "", h, flags=re.S)
h = re.sub(r"/\* COLL-JS-START \*/.*?/\* COLL-JS-END \*/\n?", "", h, flags=re.S)
if "<!--COLL-S-->" in h:
    h = re.sub(r"<!--COLL-S-->.*?<!--COLL-E-->", lambda m: HTML, h, flags=re.S)
else:
    h, n = re.subn(r'<section id="brands"[^>]*>.*?</section>', lambda m: HTML, h, count=1, flags=re.S)
    assert n == 1, "section #brands introuvable"
h = h.replace("</style>", CSS + "\n</style>", 1)
i = h.rfind("</script>")
h = h[:i] + JS.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))) + "\n" + h[i:]
(ROOT/"index.html").write_text(h, encoding="utf-8")

for g, name in (("f", "femme"), ("h", "homme")):
    ms = [m for m in data if m["g"] == g]
    print(f"{name}: {len(ms)} modèles, {sum(len(m['i']) for m in ms)} photos")
print("index.html mis à jour (sauvegarde : index.backup-collection.html)")
