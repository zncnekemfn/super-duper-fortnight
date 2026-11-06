import os, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
idx = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp", "index.html")
if not os.path.exists(idx):
    print("ABORTO: no encuentro", idx); sys.exit(1)
h = open(idx, encoding="utf-8").read()
if "GSAPMINI1" in h:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "</body>" not in h or 'id="list"' not in h:
    print("ABORTO: la mini app no tiene la estructura esperada"); sys.exit(1)
JS = r"""<!--GSAPMINI1-->
<script>
(function(){
var RM=false;try{RM=window.matchMedia("(prefers-reduced-motion: reduce)").matches}catch(e){}
if(RM)return;
function go(){
if(!window.gsap)return;
var g=window.gsap,last=0;
var st=document.createElement("style");st.textContent=".gs .card{animation:none!important}.btn,.chip,.hb{will-change:transform}";document.head.appendChild(st);
document.documentElement.className+=" gs";
function cuenta(el,pre,suf,dec){if(!el)return;var t=el.textContent,n=parseFloat(t.replace(/[^0-9,]/g,"").replace(",","."));if(isNaN(n))return;var o={v:0};g.to(o,{v:n,duration:.9,ease:"power2.out",onUpdate:function(){el.firstChild&&(el.firstChild.nodeType===3)?el.firstChild.nodeValue=pre+o.v.toFixed(dec).replace(".",",")+suf:0},onComplete:function(){el.firstChild&&(el.firstChild.nodeValue=t.split("€")[0]+"€")}})}
function tarjetas(box){
var c=box.querySelectorAll(".card");if(!c.length)return;
var now=Date.now();if(now-last<220){return}last=now;
var l=Array.prototype.slice.call(c,0,10);
g.from(l,{y:26,opacity:0,scale:.97,duration:.5,stagger:.055,ease:"power3.out",clearProps:"transform,opacity"});
l.forEach(function(x){var b=x.querySelector(".bar i");if(b){var w=b.style.width;g.fromTo(b,{width:"0%"},{width:w,duration:.8,delay:.15,ease:"power2.out"})}});
}
function hero(box){
var e=box.querySelector(".hero");if(!e)return;
g.from(e,{y:-18,opacity:0,duration:.6,ease:"power3.out",clearProps:"transform,opacity"});
g.from(e.querySelector(".bg"),{scale:1.6,opacity:0,duration:.5,delay:.2,ease:"back.out(2)",clearProps:"transform,opacity"});
var big=e.querySelector(".big");
if(big&&big.firstChild&&big.firstChild.nodeType===3){var f=big.firstChild.nodeValue,n=parseFloat(f.replace(/[^0-9,]/g,"").replace(",","."));if(!isNaN(n)){var o={v:0};g.to(o,{v:n,duration:.9,delay:.1,ease:"power2.out",onUpdate:function(){big.firstChild.nodeValue=o.v.toFixed(2).replace(".",",")+" €"},onComplete:function(){big.firstChild.nodeValue=f}})}}
}
function obs(id,fn){var el=document.getElementById(id);if(!el)return;new MutationObserver(function(){try{fn(el)}catch(e){}}).observe(el,{childList:true})}
obs("list",tarjetas);obs("favs",tarjetas);obs("hero",hero);
var tabs=document.querySelector(".tabs");
if(tabs)tabs.addEventListener("click",function(ev){var b=ev.target.closest&&ev.target.closest("button");if(!b)return;
setTimeout(function(){var s=document.querySelector("section:not(.hide)");if(s)g.from(s,{opacity:0,y:14,duration:.35,ease:"power2.out",clearProps:"transform,opacity"});
g.fromTo(b,{scale:.86},{scale:1,duration:.4,ease:"back.out(3)",clearProps:"transform"})},20)});
document.addEventListener("pointerdown",function(ev){var b=ev.target.closest&&ev.target.closest(".btn,.chip,.hb");if(b){g.to(b,{scale:.94,duration:.1,overwrite:"auto"})}},{passive:true});
["pointerup","pointercancel","pointerleave"].forEach(function(n){document.addEventListener(n,function(ev){var b=ev.target.closest&&ev.target.closest(".btn,.chip,.hb");if(b){g.to(b,{scale:1,duration:.35,ease:"back.out(3)",clearProps:"transform"})}},{passive:true})});
var h1=document.querySelector("h1");if(h1)g.from(h1,{y:-14,opacity:0,duration:.6,ease:"power3.out",clearProps:"transform,opacity"});
}
var s=document.createElement("script");s.src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js";s.async=true;s.onload=function(){try{go()}catch(e){}};s.onerror=function(){};document.head.appendChild(s);
})();
</script>
"""
bak = idx + ".bak_gsapmini1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(idx, bak)
h = h.replace("</body>", JS + "</body>", 1)
open(idx, "w", encoding="utf-8").write(h)
print("OK: animaciones GSAP añadidas a la mini app")
print("Si falla el CDN o no hay conexión, la app funciona igual (sin animar).")
print("Rollback: cp", bak, idx)
