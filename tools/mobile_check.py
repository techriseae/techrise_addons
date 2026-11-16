#!/usr/bin/env python3
"""390px mobile layout check for techriseae.com (or a local preview).

Usage: python3 tools/mobile_check.py --base http://localhost:8070 [--paths / /ar ...]
Prints one JSON line per path and exits 1 if any page is wider than 390px.
Needs google-chrome and the `websocket-client` package.
"""
import argparse, json, re, subprocess, sys, tempfile, time, urllib.request
import websocket

PORT = 9399
UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 '
      '(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
PROBE = r"""JSON.stringify((()=>{
 const iw=390, sw=Math.max(document.documentElement.scrollWidth, innerWidth);
 const over=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);
   return r.width>0&&r.right>iw+2&&r.left<iw&&s.position!=='fixed'&&!e.closest('[class*=track],[class*=marquee],.tr-hp,.o_header_language_selector')})
   .slice(0,5).map(e=>e.tagName+'.'+String(e.className).slice(0,40)+':'+Math.round(e.getBoundingClientRect().right));
 const small=[...document.querySelectorAll('header a, header button, footer a, footer button, .tr-btn, button.btn, a.btn')]
   .filter(e=>{const r=e.getBoundingClientRect();return e.offsetParent&&!e.closest('.offcanvas,.o_skip_to_content,.visually-hidden')&&getComputedStyle(e).visibility!=='hidden'&&r.width>0&&r.height>0&&r.height<40});
 const ban=document.querySelector('#tr-cookie-banner');
 const visible=!!(ban&&document.querySelector('.tr-cookie-visible'));
 let fabOverlap=false;
 const fab=document.querySelector('.tr-whatsapp-float, .tr-whatsapp, [class*=whatsapp-float], a[href*="wa.me"].position-fixed');
 const acc=document.querySelector('#tr-cookie-accept');
 if(visible&&fab&&acc){const a=fab.getBoundingClientRect(),b=acc.getBoundingClientRect();
   fabOverlap=!(a.right<b.left||a.left>b.right||a.bottom<b.top||a.top>b.bottom);}
 return {iw,sw,h:document.documentElement.scrollHeight,bannerH:visible?ban.offsetHeight:0,fabOverlap,
   smallTargets:small.length,smallSample:small.slice(0,4).map(e=>(e.textContent||e.className).trim().slice(0,30)),overflowEls:over};
})())"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--paths', nargs='*')
    ap.add_argument('--with-banner', action='store_true', help='do not pre-accept cookies')
    a = ap.parse_args()
    base = a.base.rstrip('/')
    paths = a.paths
    if not paths:
        sm = urllib.request.urlopen(base + '/sitemap.xml').read().decode()
        paths = [re.sub(r'^https?://[^/]+', '', u) or '/' for u in re.findall(r'<loc>([^<]+)</loc>', sm)]
    prof = tempfile.mkdtemp(prefix='mcheck')
    ch = subprocess.Popen(['google-chrome', '--headless=new', f'--remote-debugging-port={PORT}',
                           f'--remote-allow-origins=http://127.0.0.1:{PORT}', f'--user-data-dir={prof}',
                           '--no-first-run', '--hide-scrollbars', 'about:blank'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json')); break
            except Exception:
                time.sleep(0.3)
        ws = websocket.create_connection([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'],
                                         origin=f'http://127.0.0.1:{PORT}')
        n = [0]
        def cmd(m, **p):
            n[0] += 1; ws.send(json.dumps({'id': n[0], 'method': m, 'params': p}))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == n[0]:
                    return r.get('result', {})
        cmd('Page.enable')
        cmd('Network.setUserAgentOverride', userAgent=UA)
        cmd('Emulation.setDeviceMetricsOverride', width=390, height=844, deviceScaleFactor=2, mobile=True)
        cmd('Emulation.setTouchEmulationEnabled', enabled=True)
        if not a.with_banner:
            cmd('Page.navigate', url=base + '/'); time.sleep(3)
            cmd('Runtime.evaluate', expression='localStorage.setItem("tr_cookie_consent_v1",'
                'JSON.stringify({analytics:false,ads:false,ts:Date.now()}))')
        bad = False
        for p in paths:
            cmd('Page.navigate', url=base + p); time.sleep(6 if a.with_banner else 4)
            r = json.loads(cmd('Runtime.evaluate', expression=PROBE, returnByValue=True)['result']['value'])
            r = {'path': p, **r}
            bad |= r['sw'] > r['iw']
            print(json.dumps(r, ensure_ascii=False))
        return 1 if bad else 0
    finally:
        ch.terminate()


if __name__ == '__main__':
    sys.exit(main())
