# -*- coding: utf-8 -*-
"""
StockHunter WebApp 后端 — 还原 StockHunter Malaysia 3.7.1 全部 API 调用
逆向来源: APK dex 反编译 (Fragment_GrabStock / AskVolley / AES256Cipher)
加密: AES-256-CBC key="Kls3@p#GI3ch!qEh" iv=16x0, Base64
前端不能直接调 freeinfo.my (CORS + 需AES加密), 所以后端做代理.
"""
import base64, ssl, json, urllib.request, urllib.parse
from flask import Flask, request, jsonify, Response, send_file
from Crypto.Cipher import AES
from pathlib import Path

KEY = b"Kls3@p#GI3ch!qEh"
IV  = bytes(16)
VER = "3.7.1"
SN  = "own"

app = Flask(__name__)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def pkcs7(b):
    p = 16 - len(b) % 16
    return b + bytes([p]) * p

def aes_encode(s: str) -> str:
    c = AES.new(KEY, AES.MODE_CBC, IV)
    return base64.b64encode(c.encrypt(pkcs7(s.encode('utf-8')))).decode()

def gethashurl(base_url: str, params: str) -> str:
    """图表类 / 通用: base + ?hash=aes(params)&os=and (不含 ver/sn)"""
    return f"{base_url}?hash={urllib.parse.quote(aes_encode(params), safe='')}&os=and"

def get_screener_url(query: str) -> str:
    """screener: klsestock.com/json_filter_v1.php?hash=aes(query&ver&sn)&os=and"""
    plain = f"{query}&ver={VER}&sn={SN}"
    return f"http://www.klsestock.com/json_filter_v1.php?hash={urllib.parse.quote(aes_encode(plain), safe='')}&os=and"

def proxy_get(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "okhttp/3"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read(), r.headers.get('Content-Type', 'application/json')

def req_date():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

# ---------- API 路由 ----------
@app.route('/api/curresult')
def curresult():
    """实时行情 (getcurresult_v1.php)"""
    url = f"http://freeinfo.my/api/klse/getcurresult_v1.php?hash={urllib.parse.quote(aes_encode('req_date='+req_date()), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/api/index')
def index():
    """指数 (getklse_index_v1.php) region=index/ASEAN/ASIA/WORLD"""
    region = request.args.get('region', 'index')
    plain = f"idx_type=index&region={region}&location=&req_date={req_date()}"
    url = f"http://www.freeinfo.my/api/klse/getklse_index_v1.php?hash={urllib.parse.quote(aes_encode(plain), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/api/hotstock')
def hotstock():
    """热门股 (getklse_hotstk_v1.php) day=1/7/30"""
    day = request.args.get('day', '1')
    lang = request.args.get('lang', 'en')
    url = f"http://freeinfo.my/api/klse/getklse_hotstk_v1.php?hash={urllib.parse.quote(aes_encode(f'day={day}&Lang={lang}&req_date={req_date()}'), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/api/news')
def news():
    """新闻/社媒 (getklsenews_bycode_v2.php / getklse_social_v1.php)"""
    kind = request.args.get('kind', 'bycode')
    stk = request.args.get('stk', '')
    post = request.args.get('post', '')
    cat = request.args.get('cat', '')
    lang = request.args.get('lang', 'en')
    if kind == 'social':
        plain = f"StkCode={stk}&PostId={post}&Cat={cat}&Lang={lang}&req_date={req_date()}"
        base = "http://freeinfo.my/api/klse/getklse_social_v1.php"
    else:
        plain = f"StkCode={stk}&PostId={post}&Cat={cat}&Lang={lang}&keywId=&req_date={req_date()}"
        base = "http://www.freeinfo.my/api/klse/getklsenews_bycode_v2.php"
    url = f"{base}?hash={urllib.parse.quote(aes_encode(plain), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/api/dividend')
def dividend():
    """股息 (getklsediv_bycode_v1.php)"""
    stk = request.args.get('stk', '')
    url = f"http://www.freeinfo.my/api/klse/getklsediv_bycode_v1.php?hash={urllib.parse.quote(aes_encode(f'StkCode={stk}&req_date={req_date()}'), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/api/prospect')
def prospect():
    """业绩展望 (getklse_prospect_v1.php / bycode)"""
    bycode = request.args.get('bycode', '0')
    if bycode == '1':
        stk = request.args.get('stk', '')
        plain = f"stk_code={stk}&q_year=&PostId=&KeywId=&req_date={req_date()}&os=and"
        base = "http://www.freeinfo.my/api/klse/getklseprospect_bycode_v1.php"
    else:
        plain = f"req_date={req_date()}"
        base = "http://www.freeinfo.my/api/klse/getklse_prospect_v1.php"
    url = f"{base}?hash={urllib.parse.quote(aes_encode(plain), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/api/screener', methods=['GET', 'POST'])
def screener():
    """选股 (json_filter_v1.php @ klsestock.com)"""
    if request.method == 'POST':
        q = request.form.get('query') or request.json.get('query','')
    else:
        q = request.args.get('query', 'id=20&bo=1&yh=0&tp=0&gw=0&nc=1&iw=0&day=&type=&trend=&pri_mi=&pri_mx=&sector=')
    url = get_screener_url(q)
    data, ct = proxy_get(url)
    return Response(data, mimetype='application/json')

@app.route('/api/chart/<chart_type>')
def chart(chart_type):
    """图表 (adam/mom_subsector/happypanic) 返回 HTML, 前端用 iframe 嵌入"""
    stk = request.args.get('stk', '')
    if chart_type == 'adam':
        base = f"http://www.stockhunter.my/api/klse/get_chart_adam.php"
        params = f"StkCode={stk}&req_date={req_date()}"
        url = gethashurl(base, params)
    elif chart_type == 'mom_subsector':
        base = f"http://www.stockhunter.my/api/klse/get_chart_mom_subsector.php"
        url = gethashurl(base, f"req_date={req_date()}")
    elif chart_type == 'happypanic':
        base = f"http://www.freeinfo.my/api/klse/get_chart_happypanic.php"
        url = gethashurl(base, f"req_date={req_date()}")
    else:
        return jsonify({"error": "unknown chart_type"}), 400
    data, ct = proxy_get(url)
    return Response(data, mimetype='text/html')

@app.route('/api/checkver')
def checkver():
    url = f"http://freeinfo.my/api/klse/check_app_ver.php?hash={urllib.parse.quote(aes_encode(f'AppVersion={VER}&req_date={req_date()}'), safe='')}&os=and"
    data, ct = proxy_get(url)
    return Response(data, mimetype=ct)

@app.route('/')
def index_page():
    return send_file(Path(__file__).parent / 'templates' / 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
