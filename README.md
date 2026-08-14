# StockHunter Malaysia — WebApp Reverse Engineering & Reimplementation

> 逆向 **StockHunter Malaysia 3.7.1** (Android APK) 的全部 API 与选股(Screener)实现，并在网页端**完整复现** App 功能。
>
> 纯前端 / 零后端 / 跨平台 —— 一个 HTML 文件即可运行。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 目录

- [1. 项目简介](#1-项目简介)
- [2. 免责声明](#2-免责声明)
- [3. 逆向过程](#3-逆向过程)
- [4. API 接口总览](#4-api-接口总览)
- [5. 请求加密机制](#5-请求加密机制)
- [6. Screener 参数 Schema](#6-screener-参数-schema)
- [7. 返回数据模型](#7-返回数据模型)
- [8. WebApp 使用](#8-webapp-使用)
- [9. 部署 (CORS 代理)](#9-部署-cors-代理)
- [10. 验证结果](#10-验证结果)
- [11. API 数据分析与后端原理](#11-api-数据分析与后端原理)
- [12. API 完整参数手册](#12-api-完整参数手册)
- [13. 策略模块解密 (Strategy List)](#13-策略模块解密-strategy-list)
- [14. 文件结构](#14-文件结构)

---

## 1. 项目简介

StockHunter 是马来西亚 (Bursa Malaysia / KLSE) 股票分析 App，提供实时行情、指数、热门股、新闻、股息、技术指标、K线形态识别和**选股 Screener**。

本项目通过反编译 APK，提取出：
- 所有后端 API endpoint（行情/指数/新闻/股息/Screener/图表）
- Screener 请求的 **AES-256 加密方式**与完整参数 schema
- 返回数据的字段模型

并据此实现了一个**功能对等的网页版**，无需登录、无需官方 API key。

### 功能对照

| App 功能 | WebApp 标签 | 状态 |
|---|---|---|
| 实时行情 | 行情(SH) | ✅ |
| Yahoo 真实行情 | 实时行情(Yahoo) | ✅ |
| 指数 (马/东盟/亚/全球) | 指数 | ✅ |
| 热门股 | 热门股 | ✅ |
| 新闻 / 社媒讨论 | 新闻 | ✅ |
| 股息 | 股息 | ✅ |
| **选股 Screener** | 选股 Screener | ✅ |
| 图表 (ADAM/Momentum/Happy-Panic) | 图表 | ✅ |

---

## 2. 免责声明

⚠️ **本项目仅用于教育、安全研究和互操作 (interoperability) 学习目的。**

- 逆向工程遵循「为达成与其他软件互操作而必要的步骤」的合理使用范畴。
- 本项目**不存储、不破解、不使用任何用户凭证**；所有接口均为 App 公开调用的匿名端点。
- AES 密钥硬编码于 APK 中（即公开分发），本项目如实还原，不构成破解。
- 数据版权归 StockHunter / 原始数据源所有；本项目的 Yahoo Finance 数据来自公开 API。
- 使用者须遵守所在地区法律法规及目标服务条款。作者不对使用后果负责。

---

## 3. 逆向过程

### 工具链
- **jadx 1.5.1** (dex → Java 反编译)
- **Python + pycryptodome** (AES 验证)
- **dex 字符串表提取** (轻量定位 endpoint，无需完整反编译)

### 步骤
1. APK 无加固、双 dex（共 13.8MB），直接 jadx 反编译。
2. 从 dex 字符串表筛出全部 `http(s)://` endpoint，定位 API 域名。
3. 反编译 `Fragment_GrabStock.java` → `runVolley()` 拿到 Screener 请求构造。
4. 反编译 `AskVolley.java` + `AES256Cipher.java` → 提取 AES 密钥与加密流程。
5. 反编译 `strings.xml` → 确认 `bh_api_url = http://www.klsestock.com/`（Screener 真实 base）。
6. 用提取的密钥**实测复现**请求 → 服务端返回真实股票数据，验证成功。

### 关键发现
- Screener 走 **`bh_api_url` 资源** (`klsestock.com`)，**不是** `freeinfo.my`（后者是行情/新闻接口）。
- 所有筛选参数整体 **AES-256-CBC 加密**后放入单个 `hash` 参数，非明文 GET。
- `getCondition(key)` 方法 jadx 未能反编译（指令过多），但参数名已从 `runVolley` 完整拿到，请求已能跑通。

---

## 4. API 接口总览

| 域名 | 用途 | 主要 endpoint |
|---|---|---|
| `http://www.klsestock.com/` | **Screener 选股** | `json_filter_v1.php` |
| `http://freeinfo.my/api/klse/` | 行情/指数/热门/新闻/股息/图表 | `getcurresult_v1.php`, `getklse_index_v1.php`, `getklse_hotstk_v1.php`, `getklsenews_bycode_v2.php`, `getklsediv_bycode_v1.php`, `get_chart_happypanic.php` |
| `http://www.freeinfo.my/api/klse/` | 新闻/股息/图表/指数 | `getklsenews_bycode_v2.php`, `getklsediv_bycode_v1.php`, `getklse_index_v1.php` |
| `http://www.stockhunter.my/api/klse/` | ADAM 图表 | `get_chart_adam.php`, `get_chart_mom_subsector.php` |
| `https://query1.finance.yahoo.com/` | Yahoo 真实行情 (补充数据源) | `v8/finance/chart/<SYMBOL>` |

### 各接口请求格式（逆向自源码）

| 功能 | 方法 | URL | 参数 (加密前明文) |
|---|---|---|---|
| 行情 | GET | `freeinfo.my/.../getcurresult_v1.php` | `req_date=YYYY-MM-DD` |
| 指数 | GET | `freeinfo.my/.../getklse_index_v1.php` | `idx_type=index&region=index\|ASEAN\|ASIA\|WORLD&location=&req_date=...` |
| 热门 | GET | `freeinfo.my/.../getklse_hotstk_v1.php` | `day=1\|7\|30&Lang=en&req_date=...` |
| 新闻 | GET | `freeinfo.my/.../getklsenews_bycode_v2.php` | `StkCode=&PostId=&Cat=&Lang=en&keywId=&req_date=...` |
| 社媒 | GET | `freeinfo.my/.../getklse_social_v1.php` | `StkCode=&PostId=&Cat=&Lang=en&req_date=...` |
| 股息 | GET | `freeinfo.my/.../getklsediv_bycode_v1.php` | `StkCode=<code>&req_date=...` |
| 业绩 | GET | `freeinfo.my/.../getklse_prospect_v1.php` | `req_date=...` |
| **Screener** | GET | `klsestock.com/json_filter_v1.php` | 见 [§6](#6-screener-参数-schema) + `&ver=3.7.1&sn=<serial>` |
| ADAM图 | GET | `stockhunter.my/.../get_chart_adam.php` | `StkCode=<code>&req_date=...` (返回 HTML) |
| Yahoo | GET | `query1.finance.yahoo.com/v8/finance/chart/<SYMBOL>` | `?interval=1d&range=1mo` |

> 所有 `freeinfo.my` / `klsestock.com` / `stockhunter.my` 请求的参数均经 AES 加密后放入 `?hash=<密文>&os=and`。图表类 (`*_chart_*`) 不含 `ver`/`sn`。

---

## 5. 请求加密机制

源码 `AES256Cipher.java`：
```java
public static byte[] ivBytes = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
public static String key = "Kls3@p#GI3ch!qEh";

// AES/CBC/PKCS5Padding, Base64 输出
public static String AES_Encode(String str) {
    IvParameterSpec iv = new IvParameterSpec(ivBytes);
    SecretKeySpec sk = new SecretKeySpec(key.getBytes("UTF-8"), "AES");
    Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding");
    c.init(Cipher.ENCRYPT_MODE, sk, iv);
    return Base64.encodeToString(c.doFinal(str.getBytes("UTF-8")), 0);
}
```

**等效 Python**：
```python
from Crypto.Cipher import AES
import base64

KEY = b"Kls3@p#GI3ch!qEh"   # 硬编码于 APK
IV  = bytes(16)             # 全零

def pkcs7_pad(b):
    pad = 16 - len(b) % 16
    return b + bytes([pad]) * pad

def aes_encode(plain: str) -> str:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ct = cipher.encrypt(pkcs7_pad(plain.encode("utf-8")))
    return base64.b64encode(ct).decode("ascii")
```

**等效 JavaScript (crypto-js)**：
```javascript
function aesEncrypt(plain){
  const k  = CryptoJS.enc.Utf8.parse("Kls3@p#GI3ch!qEh");
  const iv = CryptoJS.enc.Utf8.parse("\x00".repeat(16));
  return CryptoJS.AES.encrypt(CryptoJS.enc.Utf8.parse(plain), k,
    {iv:iv, mode:CryptoJS.mode.CBC, padding:CryptoJS.pad.Pkcs7}).toString();
}
```

最终请求：
```
GET {base}?hash={encodeURIComponent(aesEncrypt(plainParams))}&os=and
```
Screener 的 `plainParams = queryString + "&ver=3.7.1&sn=<Build.SERIAL>"`（实测 `sn=own` 即可）。

---

## 6. Screener 参数 Schema

来自 `Fragment_GrabStock.runVolley()`（非 Gold 用户默认集 + Gold 字段）：

### 基础 (SA / StockHunter Analysis)
```
id=20
&bo=      突破 (breakout)        0/1
&yh=      年高 (year high)       0/1
&tp=      最高盈利 (top profit)  0/1
&gw=      黄金交叉 (golden cross) 0/1
&nc=      净现金 (net cash)      0/1
&iw=      权证 (warrant)         0/1
&day=     天数 (day count)
&type=    报告类型 (report type)
&trend=   趋势 (trend)
&pri_mi=  最低价 (price min)
&pri_mx=  最高价 (price max)
&sector=  板块 (sector)
```

### 基本面 (FA — Gold 专属)
```
&pe=       PE
&pm=       利润率 (profit margin)
&ev=       Enterprise Value
&dc=       债现比 (debt/cash)
&cr=       流动比率 (current ratio)
&ey=       盈利收益率 (earning yield)
&roe=      ROE
&dy=       股息率 (dividend yield)
&pob=      市净率 (price/book)
&m_cap_min= / &m_cap_max=   市值 min/max
&t_share_min= / &t_share_max=  总股数 min/max
```

### 技术 (TA — Gold 专属)
```
&iv=       量增 (volume up)        0/1
&macd=     MACD 信号               0/1
&macd_ab=  MACD 上/下              0/1
&rsi_c= / &rsi_v=   RSI 条件/值
&obv=      OBV
&ms=       市场信号 (market signal)
&ma1= / &ma_c1=   MA1 + 条件
&ma2= / &ma_c2=   MA2 + 条件
&ma3=               MA3
&macd_day= MACD 天数
&bb= / &bb_day=    Bollinger Band + 天数
&turn_ov_min= / &turn_ov_max=   成交额 min/max
&turn_ov_avg_min= / &turn_ov_avg_max=  平均成交额 min/max
&mom_status=   Momentum 状态 (GoldPlus)
```

**MA 映射** (`getMAF`)：
```
"0"=Price "1"=EMA10 "2"=EMA20 "3"=EMA25 "4"=EMA50
"5"=SMA10 "6"=SMA20 "7"=SMA60 "8"=SMA200
```

### K线形态 (19种 — Gold 专属，各 0/1)
```
hammer harami kicking piercing tristar dojistar haramicross
morningstar threeoutside engulfing abandonbaby dragonflydoji marubozu
upgapsidebyside invertedhammer takuri morningdojistar tasukigap
threelinestrike threewhitesoldiers
```

---

## 7. 返回数据模型

Screener 返回 JSON 数组，每只股票一个对象（实测字段节选）：
```json
{
  "stockname":"AHB","stockcode":"7315","price":"0.050","volumn":"40660700",
  "uptrend":"5","topprofit":"0","breakout":"2","daycount":"1",
  "sikl_main_sector":"CONSUMER PRODUCTS & SERVICES",
  "net_cash":"1","roe":-14.42,"profit_margin":-23.38,"pe":"-8.82",
  "dy":"0","ev":44370335,"current_ratio":113.05,"pri_of_book":1.27,
  "macd_line":"0.00353","macd_signal":"0.00218","macd":"1","rsi":"79.87",
  "obv":"8249900.00","ema10":"0.0412","ema20":"0.0370","ema50":"0.0331",
  "turnover_amt":"1996680.0000","market_cap":"45915000.00",
  "ema_golden_cross":"1","sma_golden_cross":"1",
  "mom_status":"1","mom_strength":"74.07",
  "candle_desc":"Marubozu "
}
```

完整字段约 60+（基本面 + 技术面 + K线形态 + 市场信号）。

---

## 8. WebApp 使用

### 方案 B：纯前端（推荐，零后端）
文件：`webapp/stockhunter_webapp.html`

直接双击打开**不行**（浏览器 CORS + Worker 需 Origin），需托管到任意静态站点（Netlify / Vercel / GitHub Pages / Cloudflare Pages）。

打开后：
- 选股标签 → 点预置条件（突破+净现金 / 净现金 / 低PE / MACD金叉）→ 运行选股
- 实时行情(Yahoo) → 输入 `1155.KL`（大众银行）/ `KLSE`（指数）
- 其他标签按界面提示填代码即可

### 方案 A：Flask 后端（备用，无 CORS 限制）
文件：`webapp/app.py` + `webapp/templates/index.html`
```bash
pip install flask pycryptodome
python webapp/app.py
# 浏览器打开 http://localhost:5000
```

---

## 9. 部署 (CORS 代理)

StockHunter 接口在第三方域名且**无 CORS 头**，浏览器无法直接 `fetch`。本项目的纯前端方案依赖一个 **CORS 代理**转发请求。

浏览器侧请求：
```
GET {PROXY}?url={encodeURIComponent(targetUrl)}
```

⚠️ **代理要求**：示例代理要求请求带 `Origin` header 且来自允许域（防滥用），否则返回 403。
- 网页 `fetch` 会自动带部署域的 `Origin`。
- 部署前请把 `webapp/stockhunter_webapp.html` 中 `getJSON()` 的 `Origin` 值改为你的部署域（默认 `https://stockhunter.netlify.app`）。
- 把你的 CORS 代理 URL 填入顶部 `PROXY` 常量。

**自己搭代理**（Cloudflare Worker 示例）：
```javascript
// worker.js — 允许指定域调用
export default {
  async fetch(req){
    const url = new URL(req.url).searchParams.get('url');
    const origin = req.headers.get('Origin') || '';
    const ALLOW = ['https://stockhunter.netlify.app','https://your-domain.com'];
    if(!ALLOW.includes(origin)) return new Response('forbidden',{status:403});
    const r = await fetch(url, {headers:{'User-Agent':'Mozilla/5.0'}});
    return new Response(r.body, {status:r.status, headers:{
      'Access-Control-Allow-Origin': origin,
      'Content-Type': r.headers.get('Content-Type')
    }});
  }
}
```

---

## 10. 验证结果

实测（经 CORS 代理 + 正确 Origin）：

| 接口 | 结果 |
|---|---|
| Screener (`json_filter_v1.php`) | ✅ 200，返回真实股票数组 |
| 行情 (`getcurresult_v1.php`) | ✅ 200 |
| 指数 (`getklse_index_v1.php`) | ✅ 200 |
| 热门 (`getklse_hotstk_v1.php`) | ✅ 200 |
| 新闻 (`getklsenews_bycode_v2.php`) | ✅ 200 |
| 股息 (`getklsediv_bycode_v1.php`) | ✅ 200 |
| ADAM 图 (`get_chart_adam.php`) | ✅ 200 (HTML) |
| Yahoo (`query1.finance.yahoo.com`) | ✅ 200 真实马股数据 |

AES 加密与 APK 字节级一致（key=`Kls3@p#GI3ch!qEh`，CBC，IV=0，PKCS7，Base64）。

---

## 11. API 数据分析与后端原理

详细逆向分析见 **[API_ANALYSIS.md](API_ANALYSIS.md)**：

- Screener 返回 **106 字段/股**（行情 + 基本面 + 技术 + 19种K线形态 + 牛熊阶段）
- 当前**只有 `klsestock.com` 的 Screener 与 `stockhunter.my` 图表在用**；`freeinfo.my` 那组（行情/新闻/股息）服务端返回空
- 后端推断：**PHP + MySQL**，每日批处理预计算指标 → Screener 是预计算宽表的 SQL 过滤；图表是服务端预渲染 HTML（内联数据数组）
- 加密仅为提高抓取门槛（key 硬编码公开）

---

## 12. API 完整参数手册

所有接口的**加密明文参数逐字列表** + App 截图功能映射，见 **[API_PARAMETERS.md](API_PARAMETERS.md)**。

⚠️ 关键参数坑：`Lang` 取值 `1`(英)/`2`(中)/`""`(都含)，**不是 `en`**；news 必带 `keywId`。

---

## 13. 策略模块解密 (Strategy List)

App 内 Strategy List 的 6 个策略（Growth/Sector/Trend/Report/Hot/Top），来源是 Google Play 描述里的 goo.gl 短链 → Google Slides，**已完整抓取文字内容**。每个策略对应一组 `json_cache` 预设榜单接口。

详见 **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)**。WebApp 已内置"策略"标签页渲染这 6 个策略说明。

---

## 14. 文件结构

```
stockhunter-webapp/
├── README.md                      # 本文档
├── LICENSE                        # MIT
├── .gitignore
├── webapp/
│   ├── stockhunter_webapp.html    # ⭐ 纯前端 WebApp (方案B, 主力)
│   ├── app.py                     # Flask 后端 (方案A, 备用)
│   └── templates/index.html      # Flask 前端
├── reverse_engineering/
│   ├── STOCKHUNTER_REVERSE_REPORT.md   # 详细逆向报告
│   ├── API_ANALYSIS.md                 # API 数据分析与后端原理推断
│   ├── API_PARAMETERS.md               # ⭐ 全部接口加密参数逐字 + 截图功能映射
│   ├── STRATEGY_GUIDE.md               # ⭐ 策略模块(Strategy List)完整解密
│   ├── stockhunter_extract_strings.py   # dex 字符串提取脚本
│   ├── stockhunter_dex_strings.txt       # 提取出的全部 API 字符串
│   └── stockhunter_test_screener.py      # 实测复现脚本
└── tools/
    ├── run_jadx_stockhunter.bat   # jadx 反编译命令
    └── run_jadx_res.bat           # jadx 解资源命令
```

---

## 12. 参考

- 反编译工具：[jadx](https://github.com/skylot/jadx)
- 加密库：[pycryptodome](https://github.com/Legrandin/pycryptodome) / [crypto-js](https://github.com/brix/crypto-js)
- 数据源：StockHunter Malaysia / Yahoo Finance

---

**⭐ 如果本项目对你有帮助，欢迎 Star / Fork / PR。**
