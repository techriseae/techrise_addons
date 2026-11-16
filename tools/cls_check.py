#!/usr/bin/env python3
"""Measure Cumulative Layout Shift on a page at 390px (or desktop) for N seconds.

Usage: python3 tools/cls_check.py --base http://localhost:8070 [--paths / /ar] [--secs 20] [--desktop]
Prints one JSON line per path: total CLS and the elements that moved.
Exits 1 if any page's CLS is above --max (default 0.05).
Needs google-chrome and the `websocket-client` package.
"""
import argparse, json, subprocess, sys, tempfile, time, urllib.request
import websocket

PORT = 9398
INSTALL = r"""(()=>{window.__cls=0;window.__shifts=[];
new PerformanceObserver(l=>{for(const e of l.getEntries()){if(e.hadRecentInput)continue;window.__cls+=e.value;
 window.__shifts.push({t:Math.round(e.startTime),v:+e.value.toFixed(4),src:(e.sources||[]).map(s=>{const n=s.node;
 return n&&n.nodeType===1?(n.tagName+'.'+String(n.className).slice(0,40)):String(n&&n.nodeName)})})}})
 .observe({type:'layout-shift',buffered:true});})()"""
READ = "JSON.stringify({cls:+window.__cls.toFixed(4),shifts:window.__shifts.slice(0,8)})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--paths', nargs='*', default=['/'])
    ap.add_argument('--secs', type=float, default=20)
    ap.add_argument('--max', type=float, default=0.05)
    ap.add_argument('--desktop', action='store_true')
    a = ap.parse_args()
    base = a.base.rstrip('/')
    prof = tempfile.mkdtemp(prefix='clscheck')
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
            n[0] += 1
            ws.send(json.dumps({'id': n[0], 'method': m, 'params': p}))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == n[0]:
                    return r.get('result', {})
        cmd('Page.enable')
        if a.desktop:
            cmd('Emulation.setDeviceMetricsOverride', width=1350, height=940, deviceScaleFactor=1, mobile=False)
        else:
            cmd('Emulation.setDeviceMetricsOverride', width=390, height=844, deviceScaleFactor=2, mobile=True)
        # Install the observer before any page script runs, on every navigation.
        cmd('Page.addScriptToEvaluateOnNewDocument', source=INSTALL)
        bad = False
        for p in a.paths:
            cmd('Page.navigate', url=base + p)
            time.sleep(a.secs)
            r = json.loads(cmd('Runtime.evaluate', expression=READ, returnByValue=True)['result']['value'])
            r = {'path': p, **r}
            bad |= r['cls'] > a.max
            print(json.dumps(r, ensure_ascii=False))
        return 1 if bad else 0
    finally:
        ch.terminate()


if __name__ == '__main__':
    sys.exit(main())
