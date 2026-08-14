# -*- coding: utf-8 -*-
"""StockHunter screener 实测: base=http://www.klsestock.com/ , endpoint=json_filter_v1.php
AES-256-CBC key=Kls3@p#GI3ch!qEh iv=全0, 加密 query&ver=&sn= -> hash 参数, GET ?hash=..&os=and
"""
import base64, urllib.request, ssl, urllib.parse
from Crypto.Cipher import AES

KEY=b"Kls3@p#GI3ch!qEh"; IV=bytes(16)
VER="3.7.1"; SN="own"   # Build.SERIAL 每台不同, 先用 own 试探

def pkcs7(b):
    p=16-len(b)%16; return b+bytes([p])*p
def aes_encode(s):
    c=AES.new(KEY,AES.MODE_CBC,IV)
    return base64.b64encode(c.encrypt(pkcs7(s.encode('utf-8')))).decode()

# 取非gold默认 screener 条件 (Fragment_GrabStock.runVolley str4, 非gold强制 bo=1)
str4="bo=1&yh=0&tp=0&gw=0&nc=0&iw=0&day=&type=&trend=&pri_mi=&pri_mx="
query="id=20&"+str4
plain=query+"&ver="+VER+"&sn="+SN
h=aes_encode(plain)
url_q="hash="+urllib.parse.quote(h,safe='')+"&os=and"
url="http://www.klsestock.com/json_filter_v1.php?"+url_q
print("URL:", url[:120],"...")
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
try:
    req=urllib.request.Request(url, headers={"User-Agent":"okhttp/3"})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        d=r.read(3000).decode('utf-8','ignore')
    print("HTTP", r.status)
    print("BODY:", d[:1500])
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:150])
