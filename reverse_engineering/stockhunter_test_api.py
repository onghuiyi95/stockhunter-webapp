# -*- coding: utf-8 -*-
"""复现 StockHunter screener 请求:
1) 按 Fragment_GrabStock.runVolley 构造 query string
2) AES-256-CBC (key=Kls3@p#GI3ch!qEh, iv=全0) 加密 -> base64 -> hash 参数
3) GET {base}json_filter_v1.php?hash=...&os=and
验证 base 是 freeinfo.my 还是 stockhunter.my, 看哪个返回 JSON.
"""
import base64, json, urllib.request, ssl
from Crypto.Cipher import AES

KEY = b"Kls3@p#GI3ch!qEh"          # AES256Cipher.key
IV  = bytes(16)                    # ivBytes 全0
VER = "3.7.1"                       # versionName (推测)
SN  = "own"                         # Fragment_GrabStock.huntID="own"; serial 待定, 先用 own

def pkcs7(b):
    pad = 16 - len(b)%16
    return b + bytes([pad])*pad

def aes_encode(plain: str) -> str:
    c = AES.new(KEY, AES.MODE_CBC, IV)
    return base64.b64encode(c.encrypt(pkcs7(plain.encode('utf-8')))).decode()

# 来自 runVolley 的非gold用户默认 str4 (第452行)
# 非gold: str3 = "id=20&" + str4 ; str4 默认 bo=0&yh=0&... 但非gold且全0时强制 bo=1
str4 = "bo=1&yh=0&tp=0&gw=0&nc=0&iw=0&day=&type=&trend=&pri_mi=&pri_mx="
query = "id=20&" + str4
plain = query + "&ver=" + VER + "&sn=" + SN
print("明文:", plain)
h = aes_encode(plain)
print("hash :", h[:80], "...")
url_q = "hash=" + urllib.parse.quote(h, safe='') + "&os=and"

bases = [
    "http://freeinfo.my/api/klse/",
    "http://www.freeinfo.my/api/klse/",
    "http://stockhunter.my/api/klse/",
    "http://www.stockhunter.my/api/klse/",
]
import urllib.parse
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
for base in bases:
    url = base + "json_filter_v1.php?" + url_q
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"StockHunter/Android"})
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            data = r.read(3000).decode('utf-8','ignore')
        print(f"\n[{base}] HTTP {r.status}")
        print("  ", data[:300])
    except Exception as e:
        print(f"\n[{base}] ERR {type(e).__name__}: {str(e)[:120]}")
