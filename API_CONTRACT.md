# StockHunter API 合约（传什么 / 返什么）

逆向来源：StockHunter Malaysia 3.7.1 APK（jadx）+ Python 直连实测。
所有请求经 AES-256-CBC 加密：key=`Kls3@p#GI3ch!qEh`，iv=16×0x00，PKCS5Padding，Base64。
服务端要求 `req_date` = **明天**（本机今天+1天），今天/过去均拒。

---

## 一、GET 接口（参数拼进 URL `?hash=<AES>&os=and`）

### 1. news（个股/全局新闻）
- **URL**: `http://www.freeinfo.my/api/klse/getklsenews_bycode_v2.php`
- **传**: `StkCode=<代码|空>&PostId=&Cat=&Lang=1|2&keywId=<代码|空>&req_date=<明天>`
- **返**: `{is_success:true, result_value:[{title, date, source, summary, ...}]}`（实测 10 条）
- **实测**: ✅ 活

### 2. social（社媒讨论源）
- **URL**: `http://freeinfo.my/api/klse/getklse_social_v1.php`
- **传**: `StkCode=<空>&PostId=&Cat=&Lang=1&req_date=<明天>`
- **返**: `{is_success, result_value:[{...}]}`（实测 5 条）
- **实测**: ✅ 活

### 3. hotstock（热门股票）
- **URL**: `http://freeinfo.my/api/klse/getklse_hotstk_v1.php`
- **传**: `day=1|7|30&Lang=1&req_date=<明天>`（day=1日/7周/30月）
- **返**: **裸数组** `[{stk_code, stk_name, stk_desc_en, ...}]`（实测 3730 字节，LPI 等）
- **实测**: ✅ 活（注意：返回不是 {is_success} 包装，是直接数组）

### 4. index（指数）
- **URL**: `http://www.freeinfo.my/api/klse/getklse_index_v1.php`
- **传**: `idx_type=index&region=ASIA|ASEAN|WORLD|MALAYSIA&location=&req_date=<明天>`
- **返**: `{is_success, result_value:[{name, point, chg, chg_pct, ...}]}`（实测 4 条）
- **实测**: ✅ 活（今天/过去日期返回 `Invalid token. Please correct your date and time`）

### 5. screener（选股 / 个股详情宽表）
- **URL**: `http://www.klsestock.com/json_filter_v1.php`
- **传**: `id=20&<SA/FA/TA/CA 筛选条件>&ver=3.7.1&sn=own`
  - SA: `bo/yh/tp/gw/nc/iw/tr/hl/er`（1/0 信号）
  - FA: `pe/pm/ev/dc/cr/ey/roe/dy/pob/evalue_ab/m_cap(_min/_max)/t_share(_min/_max)`（带 </> 阈值留空=不限）
  - TA: `ma1+ma_c1 / ma2+ma_c2 / ma3 / macd+macd_day / rsi_c+rsi_v / obv / bb+bb_day / turn_ov(_min/_max)`
  - CA: 19 种 K 线形态 `hammer/harami/haramicross/engulfing/piercing/dojistar/dragonflydoji/marubozu/invertedhammer/takuri/morningstar/morningdojistar/tristar/kicking/tasukigap/abandonbaby/threelinestrike/threeoutside/threewhitesoldiers`
- **返**: **裸数组** 1096 只 × 106 字段 `[{stockcode, stockname, price, pe, roe, dy, macd, rsi, pri_ma20, pri_ma200, qm, qtoq, profit_margin, ...}]`
- **实测**: ✅ 活（2.2MB）。**个股详情数据全来自此表**（price/pe/roe/dy/macd/rsi/ma 等）

### 6. curresult（实时报价——已空）
- **URL**: `http://freeinfo.my/api/klse/getcurresult_v1.php`
- **传**: `req_date=<明天>`
- **返**: `{is_success:true, result_value:[]}`（活但 0 条，服务端无数据）
- **实测**: ⚠️ 空（报价改从 screener 宽表 price 字段取）

---

## 二、POST 接口（参数放 body `hash=<AES>&os=and`，Volley getParams）

> ⚠️ 关键：这些接口**必须用 POST**，且 `hash` 在请求 body（不是 URL）。
> 之前网页经 Cloudflare Worker 代理调 POST 返回空——是**代理不支持 POST 转发**，非接口停。
> Python 直连 POST 实测全部通。

### 7. DIVIDEND（股息）
- **URL**: `http://www.freeinfo.my/api/klse/getklsediv_bycode_v1.php`
- **方法**: POST
- **传(body)**: `hash=<AES("StkCode=<代码>&req_date=<明天>")>&os=and`
- **返**: `{is_success:true, result_value:[{id, r_date, f_year, ex_date, pay_date, en_date, en_type, div_cent, stk_list:[...]}]}`
  - `en_type`: "First Interim Dividend" 等
  - `div_cent`: 每股派息（分）
  - `f_year`: 财政年 "2026-12-31"
- **实测**: ✅ 直连 POST 活（MAXIS 返回 4 期股息）

### 8. Q-RESULT（季报）
- **URL**: `http://www.freeinfo.my/api/klse/getklseprospect_bycode_v1.php`
- **方法**: POST
- **传(body)**: `hash=<AES("stk_code=<代码>&q_year=<当年>&PostId=&KeywId=&req_date=<明天>")>&os=and`
- **返**: `{is_success:false, result_value:"", err_msg:"No data found."}` 或成功时 `{result_value:[{desc, ...季报序列}]}`
- **实测**: ⚠️ 接口活但**当前无数据**（返回 No data）——App 截图数据是历史缓存

### 9. WARRANT（权证）
- **URL**: `http://www.klsestock.com/json_cache_v2.php`
- **方法**: POST
- **传(body)**: `hash=<AES("id=38&code=<代码>&ver=3.7.1&sn=own")>&os=and`
- **返**: `{result_value:[{code, name, price, chg_pct, volume, ...}]}` 或空
- **实测**: ⚠️ 直连 POST 返回空（该 id=38 数据源可能下线）

---

## 三、图表接口（GET，返回 HTML/JS 图表）

### 10. ADAM 图表
- **URL**: `http://www.stockhunter.my/api/klse/get_chart_adam.php`
- **传**: `StkCode=<代码>&req_date=<明天>`

### 11. Momentum 图表
- **URL**: `http://www.stockhunter.my/api/klse/get_chart_mom_subsector.php`
- **传**: `req_date=<明天>`

### 12. Happy-Panic 图表
- **URL**: `http://www.freeinfo.my/api/klse/get_chart_happypanic.php`
- **传**: `req_date=<明天>`

---

## 四、总结

| 接口 | 方法 | 加密 | 实测 | 返回格式 |
|---|---|---|---|---|
| news | GET | URL hash | ✅ | {is_success, result_value[]} |
| social | GET | URL hash | ✅ | {is_success, result_value[]} |
| hotstock | GET | URL hash | ✅ | 裸数组[] |
| index | GET | URL hash | ✅ | {is_success, result_value[]} |
| screener | GET | URL hash | ✅ | 裸数组[]（1096×106） |
| curresult | GET | URL hash | ⚠️空 | {is_success, result_value:[]} |
| **dividend** | **POST** | **body hash** | ✅直连 | {is_success, result_value[{f_year,ex_date,pay_date,en_type,div_cent}]} |
| **qresult** | **POST** | **body hash** | ⚠️无数据 | {is_success:false, err_msg:No data} |
| **warrant** | **POST** | **body hash** | ⚠️空 | {result_value[]} |
| chart×3 | GET | URL hash | ✅ | HTML 图表 |

**关键修正（本会话）**：
1. 所有接口 `req_date` 必须传**明天**（服务端时区偏移校验）
2. news/index/hot/screener 用 **GET**（URL 拼 hash）
3. dividend/qresult/warrant 用 **POST**（body 放 hash）——之前误用 GET 导致空响应
4. 之前网页经 Worker 代理调 POST 全空 = **代理不支持 POST**，直连 POST 全通
