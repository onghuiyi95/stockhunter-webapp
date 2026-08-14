# StockHunter 后端运作方式还原 (Backend Architecture Reverse-Engineering)

> 本文回答三个核心问题（用户原始需求）：
> **1) API 返回了什么数据？ 2) 背后怎么运作的？ 3) 用什么数据库？**
>
> 基于 dex 反编译 + 实机抓包 + 真实返回结构分析。推断部分标注 ⚠️。

---

## 一、API 返回了什么数据（按业务分层的真实证据）

### 1.1 行情类 — `getcurresult_v1`
返回单只/批量股票的实时报价快照：
`price / pri_open / pri_prv_close / pri_chg / pri_chg_pcn / volumn / turnover_amt / total_share / market_cap / sikl_main_sector / scid / is_w / is_top_cap`

### 1.2 选股类 — `json_filter_v1.php` (screener)
**106 字段/股**，分 5 维（实测 AHB/7315 样本）：
- 行情：price/pri_open/pri_prv_close/volumn/turnover_amt/market_cap/sector
- 基本面：pe/roe/profit_margin/ev/EV_EBIT/earning_yield/dy/debt_cash/current_ratio/pri_of_book/net_cash/pn17
- 技术：pri_ma10~200 / ema10~60 / ema_golden_cross / macd_line/signal/daycount / rsi / obv/obv20/obv_sid / pri_bb*/market_s/ mom_status/mom_strength
- 形态：candle_* (19种, 0~100 置信度) + candle_desc
- 信号：uptrend/topprofit/breakout/daycount/HL

### 1.3 榜单类 — `json_cache_v1/v2.php?id=N`
返回**预计算好的股票列表**（已排序/过滤），字段同 screener 子集：
`stk_code / stockname / price / chg_pct / volume / pe / dy / roe / margin`
不同 `id` 对应不同榜单（Overview/Top Gainer/Loser/Growth/Trend/Hot/Report/Sector/Warrant…）。

### 1.4 新闻类 — `getklsenews_bycode_v2` / `getklse_social_v1`
**news** 返回文章流：
`id / title / desc / keywords / web_url / image_url / source / date`
**social** 返回**社媒源分类 + 每源讨论数**（关键证据）：
```json
{"Cat":"s","brand_id":70,"title":"9shares","title_cn":"9点股票","TotalQty":"11","SortSeq":2},
{"Cat":"s","brand_id":93,"title":"The Storm Media","title_cn":"風傳媒","TotalQty":"1",...},
{"Cat":"s","brand_id":48,"title":"i3investor","title_cn":"i3投资者","TotalQty":"0",...},
{"Cat":"s","brand_id":62,"title":"Blogger","title_cn":"部落格","TotalQty":"0",...}
```
→ 证明后端有 **brand/source 映射表 + 每源文章计数**，且按 `TotalQty`/`SortSeq` 排序。

### 1.5 图表类 — `get_chart_adam.php` 等
返回**完整 HTML**（Google Charts 渲染），内联数据数组：
`var sync_date=[...] / var pri_open=[...] / var pri_dy_high=[...] / var pri_close_adam_a=[...]`
→ 服务端**预计算 K线 + ADAM 指标 → 拼装 HTML 模板**（server-side rendering）。

### 1.6 统一响应壳
所有 JSON 接口包统一外壳：
```json
{"is_success":true,"result_value":[...],"err_msg":null}
```
→ 服务端有**统一 API wrapper**（PHP 中间件），对所有 endpoint 套壳。

---

## 二、背后怎么运作（数据处理管线推断）

### 2.1 请求流（实测确认）
```
App ──AES-256-CBC(key=Kls3@p#GI3ch!qEh, iv=0)──> hash 参数
   └─> GET {BASE}?hash=<密文>&os=and
       服务端: 解密 hash → 读参数 → 查库/计算 → 套 JSON 壳 或 拼 HTML
```
- 加密目的：**防抓包重放 + 防盗用**（key 硬编码公开，仅提高门槛）
- `&ver=3.7.1&sn=<serial>` 拼在明文里 → 疑似**设备/版本灰度**标识

### 2.2 两套接口体系（架构关键）
| 体系 | 加密 | 用途 | 服务端特征 |
|---|---|---|---|
| **Screener** `json_filter_v1.php` | AES | 用户自定义条件选股 | 参数化查询 |
| **Cache** `json_cache_v1/v2.php?id=N` | **明文** | 预设榜单/统计 | 静态预生成列表 |

→ 推断：**Cache 体系是 Screener 计算结果的物化视图**（materialized view）。每天算完所有股票指标后，按各种维度（Top Gainer/Profit/NetCash/Growth…）预先排序生成固定列表，存成 `json_cache`。

### 2.3 每日批处理管线（⚠️ 推断，证据强）
Screener 返回 106 字段且含**实时计算的技术指标**（MACD/RSI/布林/金叉/19种形态/动量/牛熊），服务端不可能每次请求实时算全市场 1000 只股票。推断后端有 **cron 批处理**：

```
[每日收盘后]
1. 拉取 Bursa 行情 (OHLCV) + 财务季报
2. 计算技术指标 (MACD/RSI/OBV/布林/MA/EMA)
3. 计算形态识别 (19种K线打分)
4. 计算财务比率 (PE/ROE/EV/EBIT/股息率/流动比)
5. 生成预计算宽表 stock_metrics (每只股票×每日一行)
6. 跑预设筛选 → 生成 json_cache 各 id 列表
7. 新闻/社媒：爬取 i3investor/theedgemarkets 等 → 解析 → 存 news 表 + brand 计数
```

**证据支撑**：
- `candle_*` 是 0~100 置信度（打分模型，非硬规则）→ 离线批量计算
- `macd_daycount:15` / `pri_bb_daycount:2` 带信号持续天数 → 状态机，需历史序列
- social 的 `TotalQty` 需聚合计数 → ETL 批处理
- chart 接口直接返回内联数据 HTML → 服务端预渲染

### 2.4 数据来源（⚠️ 推断）
| 数据 | 来源推断 |
|---|---|
| OHLCV 历史/实时 | Bursa Malaysia 行情 feed（经纪商/数据商 API） |
| 财务 (PE/ROE/EV/dividend) | 季报爬取（Bursa MBRS / 公司公告）或财经数据商 |
| 板块分类 | Bursa 官方 sector 映射 |
| 新闻/社媒 | i3investor / theedgemarkets / Blogger RSS 爬取（social 接口已证实这些源） |

---

## 三、用什么数据库（⚠️ 推断，基于字段与架构）

### 3.1 判断：关系型数据库 (MySQL/MariaDB)
证据链：
- 全部 endpoint 是 `.php` → **LAMP 栈**（Linux+Apache+MySQL+PHP）
- 蛇形命名（`stk_code`/`pri_now`/`sikl_main_sector`）→ MySQL 惯例
- 统一 `is_success/result_value/err_msg` 壳 → PHP 框架统一响应
- Screener 多维度 `WHERE` 过滤 → 典型 SQL 查询
- `json_cache` 是按 id 物化的查询结果的表/视图

### 3.2 推测的表结构
```sql
-- 主表
stocks (stk_code PK, stockname, sikl_main_sector, scid, is_w, total_share, ...)

-- 日行情 (实时快照, 按 req_date 查)
daily_quote (stk_code FK, trade_date, pri_open, pri_high, pri_low, pri_now,
             volumn, turnover_amt, pri_prv_close, ...)

-- 财务 (季度)
financials (stk_code FK, qm(季度月), pe, roe, profit_margin, ev, EV_EBIT,
            earning_yield, dy, debt_cash, current_ratio, pri_of_book, net_cash, pn17, ...)

-- 预计算技术指标 (日, 批处理生成)  ← Screener 主数据源
tech_indicators (stk_code FK, trade_date, pri_ma10..ma200, ema10..ema60,
                 ema_golden_cross, macd_line, macd_signal, macd_daycount,
                 rsi, obv, obv20, obv_sid, pri_bb_up, pri_bb_down, pri_bb_daycount,
                 market_s, mom_status, mom_strength, ...)

-- 形态识别 (日)
candle_patterns (stk_code FK, trade_date, candle_hammer, candle_harami, ...(19),
                 candle_desc)

-- 新闻/社媒
news (id PK, stk_code, title, desc, keywords, web_url, image_url, source, date, cat)
social_brand (brand_id PK, title, title_cn, sortseq)   -- 社媒源映射
news_brand_count (brand_id FK, stk_code, TotalQty)      -- 每源计数

-- 预设榜单 (json_cache 后端)
cache_lists (id PK, params, generated_at)  -- id=N 对应物化列表

-- 图表预渲染
chart_adam_cache (stk_code FK, trade_date, sync_date[], pri_open[], ...)  -- 内联数组源
```

### 3.3 缓存层
- 多数接口按 `req_date` 查快照表（`WHERE trade_date=?`），非实时计算 → **每日快照表**
- `json_cache` 是查询结果的**预生成物化列表**（避免每次 `ORDER BY ... LIMIT` 全表扫）
- 图表 HTML 可能带 CDN 缓存（`Cache-Control: no-cache` 头见于 chart 响应）

---

## 四、对"复现整个 APK"的启示

要完整复刻 StockHunter 后端，需自建等价管线：
```
[Yahoo Finance / Bursa feed] → 拉 OHLCV
        ↓
[指标计算引擎] → MACD/RSI/布林/OBV/MA/EMA/19形态 (Python pandas/ta)
        ↓
[MySQL 宽表] → stock_metrics (日更新)
        ↓
[API 层] → /screener (参数化SQL) + /json_cache (物化列表) + /news (爬取)
        ↓
[前端] → 纯 HTML/JS (本项目已做)
```
即：本项目网页版是**前端还原**，完整复刻还需一个**后端 + 定时任务**补上上述管线。

---

*分析日期：2026-08-14 · 数据来自真实 API 抓包（经用户 Cloudflare Worker 代理）· 架构/数据库部分为逆向推断，标注 ⚠️*
