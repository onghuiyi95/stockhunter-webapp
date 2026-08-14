# -*- coding: utf-8 -*-
"""从 StockHunter Malaysia 两个 dex 抽全部字符串, 筛 API/URL/endpoint 相关.
轻量, 不需 jadx. 直接命中 API 线索.
"""
import struct, re, zipfile
from pathlib import Path

APK = r"C:\Users\Administrator\AppData\Local\hermes\cache\documents\doc_d5117e0e61d4_StockHunter Malaysia 3.7.1.apk"
OUT = r"C:\Users\Administrator\ai-shisho\stockhunter_dex_strings.txt"

def read_uleb128(b, off):
    r, s = 0, 0
    while True:
        x = b[off]; off += 1
        r |= (x & 0x7f) << s
        if not (x & 0x80): break
        s += 7
    return r, off

def dex_strings(path):
    d = open(path,'rb').read()
    if d[:3] != b'dex': return []
    sns = struct.unpack_from('<I', d, 56)[0]
    sof = struct.unpack_from('<I', d, 60)[0]
    out = []
    for i in range(sns):
        o = struct.unpack_from('<I', d, sof+i*4)[0]
        _, st = read_uleb128(d, o)
        e = d.index(b'\x00', st)
        out.append(d[st:e].decode('utf-8','ignore'))
    return out

z = zipfile.ZipFile(APK)
allstr = []
for dex in ['classes.dex','classes2.dex']:
    raw = z.read(dex)
    tmp = Path(r"C:\Users\Administrator\AppData\Local\Temp")/dex
    tmp.write_bytes(raw)
    ss = dex_strings(str(tmp))
    allstr += ss
    print(f"{dex}: {len(ss)} 字符串")

# 去重保留
uniq = sorted(set(allstr))
# 筛 API 相关
pat = re.compile(r'(https?://|/api/|/v\d+/|base_?url|endpoint|api\.|screener|\.php|\.json|retrofit|okhttp|volley|host|domain|\.com|\.my|\.net)', re.I)
api = [s for s in uniq if pat.search(s) and 2 < len(s) < 300]
# 只打印看起来像 URL/endpoint 的
url_like = [s for s in api if re.search(r'(https?://|/api/|/v\d|screener|/stock|/quote|/screen|stock_|getStock|search)', s, re.I)]

with open(OUT,'w',encoding='utf-8') as f:
    f.write(f"# StockHunter dex 字符串 (API相关) 共 {len(api)} 命中\n\n")
    f.write("=== URL/endpoint-like ===\n")
    for s in url_like: f.write(s+"\n")
    f.write("\n=== 其他 API 关键词命中 ===\n")
    for s in api:
        if s not in url_like: f.write(s+"\n")

print(f"\n去重字符串: {len(uniq)}")
print(f"API 相关命中: {len(api)} (其中 URL-like: {len(url_like)})")
print(f"-> {OUT}")
