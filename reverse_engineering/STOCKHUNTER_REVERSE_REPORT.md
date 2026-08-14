# StockHunter Malaysia 3.7.1 — API & Screener 逆向报告

> 来源: `StockHunter Malaysia 3.7.1.apk` (10.9MB, 无加固, 2个明文dex)
> 方法: jadx 1.5.1 反编译 + dex 字符串表 + 实测复现 (已成功返回真实股票数据)
> 结论: ✅ 网页版可 100% 复现

---

## 1. 接口总览

| 域名 | 用途 | 示例 endpoint |
|---|---|---|
| `http://freeinfo.my/api/klse/` | 行情/新闻/图表/指数/自选 | `getcurresult_v1.php`, `getklse_hotstk_v1.php`, `getklsenews_bycode_v2.php`, `get_chart_happypanic.php` |
| `http://www.klsestock.com/` | **Screener 选股** (bh_api_url) | `json_filter_v1.php` ⭐ |
| `http://stockhunter.my/api/klse/` | 部分图表 (mom_subsector) | `get_chart_adam.php`, `get_mom_subsector.php` |
| `http://klsegroup.com/` | 板块 JSON | `get_json.php?id=2&sector=`, `json_cache_v1.php` |

**Screener 真端点**: `http://www.klsestock.com/json_filter_v1.php`

---

## 2. 请求机制 (核心)

### 2.1 加密
所有筛选参数**不是明文 GET 参数**，而是整体 AES 加密后放进单个 `hash` 参数：

```
源码 (Fragment_GrabStock.runVolley + AskVolley.request):
  plain = query_string + "&ver=" + versionName + "&sn=" + Build.SERIAL
  hash  = AES256Cipher.AES_Encode(plain)   // AES/CBC/PKCS5Padding, Base64
  url   = bh_api_url + "json_filter_v1.php" + "?" + URLEncodedUtils("hash="+hash, "os"="and")

源码 (AES256Cipher.java):
  key  = "Kls3@p#GI3ch!qEh"     // 硬编码
  iv   = 16字节全0
  algo = "AES/CBC/PKCS5Padding"
  out  = Base64(cipher.doFinal(plain.getBytes("UTF-8")))
```

### 2.2 完整请求示例 (实测通过)
```
GET http://www.klsestock.com/json_filter_v1.php?hash=<base64 AES>&os=and
```
无参数时返回 `{"OS":"NA"}`。带正确 hash 返回 JSON 数组（每只股票一个对象）。

### 2.3 versionName / serial
- `ver` = APK versionName (实测 "3.7.1" 服务端接受)
- `sn` = `Build.SERIAL`（每台设备不同）。实测用 `"own"` 也能返回数据，服务端对 sn 校验宽松。

---

## 3. Screener 参数 Schema (query_string 明文结构)

来自 `Fragment_GrabStock.runVolley()` 第452-476行（非Gold用户默认集）:

**基础 (SA/StockHunter Analysis 标签):**
```
id=20
&bo=   (breakout 突破)
&yh=   (year high 年高)
&tp=   (top profit 最高盈利)
&gw=   (golden cross? / 黄金交叉)
&nc=   (net cash 净现金)
&iw=   (is warrant 是否权证)
&day=  (day count 天数)
&type= (report type 报告类型)
&trend=(趋势)
&pri_mi=(price min 最低价)
&pri_mx=(price max 最高价)
&sector=(板块)
```

**Fundamental (Gold用户才加, FA 标签):**
```
&pe=   (PE)
&pm=   (profit margin 利润率)
&ev=   (Enterprise Value)
&dc=   (debt/cash 债现比)
&cr=   (current ratio 流动比率)
&ey=   (earning yield 盈利收益率)
&roe=  (ROE)
&dy=   (dividend yield 股息率)
&pob=  (price/book 市净率)
&evalue_ab= / &evalue=   (enterprise value 相关)
&m_cap_min= / &m_cap_max=   (市值 min/max)
&t_share_min= / &t_share_max=  (总股数 min/max)
```

**Technical (Gold用户, TA 标签):**
```
&iv=    (is volume up 量增)
&macd=  (MACD 信号)
&macd_ab=(MACD above/below)
&rsi_c= / &rsi_v=   (RSI 条件/值)
&obv=   (OBV)
&ms=    (market signal 市场信号)
&ma1= &ma_c1=   (MA1 + 条件)
&ma2= &ma_c2=   (MA2 + 条件)
&ma3=             (MA3)
&macd_day=        (MACD 天数)
&bb=  &bb_day=    (Bollinger Band + 天数)
&ma_conditions=   (MA 组合条件, 见下)
&turn_ov_min= / &turn_ov_max=        (成交额 min/max)
&turn_ov_avg_min= / &turn_ov_avg_max= (平均成交额 min/max)
&mom_status=      (Momentum 状态, GoldPlus 专属)
```

**Candlestick 形态 (Gold用户, 19种, 拼接):**
```
&hammer= &harami= &kicking= &piercing= &tristar= &dojistar= &haramicross=
&morningstar= &threeoutside= &engulfing= &abandonbaby= &dragonflydoji=
&marubozu= &upgapsidebyside= &invertedhammer= &takuri= &morningdojistar=
&tasukigap= &threelinestrike= &threewhitesoldiers=
```
(每个取值 0/1，勾选=1)

**MA 条件映射 (getMAF):**
```
"0"=Price "1"=EMA10 "2"=EMA20 "3"=EMA25 "4"=EMA50
"5"=SMA10 "6"=SMA20 "7"=SMA60 "8"=SMA200
```

---

## 4. 返回数据模型 (实测一只股票字段)

```json
{
  "stockname":"AHB","stockcode":"7315","price":"0.050","volumn":"40660700",
  "uptrend":"5","topprofit":"0","toprev":"0","breakout":"2","daycount":"1",
  "sikl_main_sector":"CONSUMER PRODUCTS & SERVICES",
  "profit_continue_growth":"0","ytoy":"0","qtoq":"0","priceyest":0.045,
  "stk_code":"7315","pri_open":"0.045","pri_chg":"+0.005","pri_chg_pcn":"+11.11%",
  "pri_now":"0.050","vol_now":"40660700","pri_prv_close":"0.045","HL":"1","is_w":"0",
  "er":"0","volume_up":1,"price_adj":0.005,"price_adjp":11.11,
  "report_type":1,"dy":"0","dy_status":0,"net_cash":"1","roe":-14.42,
  "profit_margin":-23.38,"pe":"-8.82","EV_EBIT":-8.65,"ev":44370335,
  "earning_yield":-11.56,"debt_cash":0,"current_ratio":113.05,"pri_of_book":1.27,
  "scid":"22","dp":"","qm":"Mar","pn17":"0","gapup":"0.000","is_30":"0",
  "macd_line":"0.00353","macd_signal":"0.00218","macd_sid":1,"macd_above":1,
  "macd":"1","macd_daycount":15,"rsi":"79.87","obv":"8249900.00","obv20":"2984040.00",
  "obv_sid":1,"market_s":"3.Bear to Bull","market_sid":1,
  "pri_ma10":"0.0400","pri_ma20":"0.0348","pri_ma60":"0.0307","pri_ma50":"0.32",
  "pri_ma200":"0.0328","ema10":"0.0412","ema20":"0.0370","ema25":"0.0358",
  "ema50":"0.0331","ema60":"0.0327","turnover_amt":"1996680.0000",
  "turnover_amt_avg":"122829.0000","total_share":"918300000.0",
  "market_cap":"45915000.00","is_top_cap":"0","ema_golden_cross":"1",
  "sma_golden_cross":"1","mom_status":"1","mom_strength":"74.07",
  "is_mom_plus_today":"0","pri_tp":"-0.061","pri_potential":"-410.00",
  "candle_desc":"Marubozu "
}
```

---

## 5. 网页版复现 — Python 示例

```python
import base64, urllib.request, urllib.parse
from Crypto.Cipher import AES

KEY=b"Kls3@p#GI3ch!qEh"; IV=bytes(16)

def pkcs7(b):
    p=16-len(b)%16; return b+bytes([p])*p

def aes_encode(s):
    c=AES.new(KEY,AES.MODE_CBC,IV)
    return base64.b64encode(c.encrypt(pkcs7(s.encode('utf-8')))).decode()

# 构造筛选条件 (示例: 突破+净现金, 非gold用户默认集)
query="id=20&bo=1&yh=0&tp=0&gw=0&nc=1&iw=0&day=&type=&trend=&pri_mi=&pri_mx=&sector="
plain=query+"&ver=3.7.1&sn=own"
h=aes_encode(plain)
url="http://www.klsestock.com/json_filter_v1.php?"+\
    "hash="+urllib.parse.quote(h,safe='')+"&os=and"
req=urllib.request.Request(url, headers={"User-Agent":"okhttp/3"})
with urllib.request.urlopen(req, timeout=25) as r:
    data=r.read().decode()
import json; print(json.loads(data)[:3])   # 前3只股票
```

## 6. 网页版复现 — JavaScript 示例

```javascript
// 需要 crypto-js
const CryptoJS = require('crypto-js');
const KEY = CryptoJS.enc.Utf8.parse('Kls3@p#GI3ch!qEh');
const IV  = CryptoJS.enc.Utf8.parse('\x00'.repeat(16)); // 16字节0
function aesEncode(plain){
  const p = CryptoJS.enc.Utf8.parse(plain);
  const opt = { iv: IV, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 };
  return CryptoJS.AES.encrypt(p, KEY, opt).toString(); // 默认 Base64
}
const query = "id=20&bo=1&yh=0&tp=0&gw=0&nc=1&iw=0&day=&type=&trend=&pri_mi=&pri_mx=&sector=";
const plain = query + "&ver=3.7.1&sn=own";
const hash = aesEncode(plain);
const url = `http://www.klsestock.com/json_filter_v1.php?hash=${encodeURIComponent(hash)}&os=and`;
fetch(url).then(r=>r.json()).then(d=>console.log(d));
```

---

## 7. 关键文件 (已归档到 stockhunter_tools/)
- `stockhunter_extract_strings.py` — dex 字符串提取
- `stockhunter_test_screener.py` — 实测复现脚本 (成功)
- `stockhunter_dex_strings.txt` — 全部 API 字符串
- 反编译源码: `stockhunter_out/sources/stockhunter/klse/my2/`
  - `TabbedDialog_Filter.java` — screener UI 编排
  - `Fragment_GrabStock.java` — **核心**: `runVolley()` 构造请求 (第436-505行)
  - `AskVolley.java` — HTTP + AES 加密
  - `AES256Cipher.java` — **密钥**: `Kls3@p#GI3ch!qEh`
  - `FilterFragment_v2.java` — 条件构建 (checkbox→JSON)

## 8. 诚实边界
- ✅ base URL、endpoint、加密方式、参数 schema、返回模型 — 全部从源码确认 + 实测复现成功
- ⚠️ `getCondition(key)` 方法 jadx 未能反编译 (4232条指令, 标记 not decompiled)，但**参数名** (bo/yh/tp/pe/macd/rsi...) 已从 `runVolley` 完整拿到。每个 key 的具体取值逻辑 (0/1/阈值) 需要 `--show-bad-code` 重反编译才能100%确认，但请求已能跑通返回数据
- ⚠️ Gold/GoldPlus 专属字段 (FA/TA 标签) 需 `golduser=true` 才拼进请求；服务端是否按账户鉴权未知 (实测用非gold默认集已返回数据)
- ⚠️ `sn` (Build.SERIAL) 实测用 "own" 即可，服务端未严格校验
