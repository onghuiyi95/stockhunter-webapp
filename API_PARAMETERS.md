# StockHunter API 完整参数手册 (All Encrypted Parameters)

> 逆向自 `StockHunter Malaysia 3.7.1` dex + **App 实机截图核对**。
> 2026-08-14 更新：实测确认 freeinfo.my 接口全部存活（之前"已退役"判断错误，真实原因是 `Lang=en` 参数错 + 漏 `keywId`）。

---

## 0. 加密统一规则

所有参数整体加密，**非明文 GET 参数**：
```
明文 = 接口特定参数字符串
密文 = AES-256-CBC( key="Kls3@p#GI3ch!qEh", iv=16×0x00, PKCS7 ) → Base64
请求 = {BASE_URL}?hash={urlencode(密文)}&os=and
```
- `key` 硬编码于 `AES256Cipher.java`
- `iv` = 全零
- `os=and` 固定（标识 Android）
- screener 额外拼 `&ver=3.7.1&sn=<serial>`（实测 `sn=own` 放行）

---

## 1. 全部接口 + 明文参数（逐字）

| # | 功能 | BASE_URL | 明文参数 (明文，加密前) |
|---|---|---|---|
| 1 | 行情 | `http://freeinfo.my/api/klse/getcurresult_v1.php` | `req_date=YYYY-MM-DD` |
| 2 | 指数 | `http://www.freeinfo.my/api/klse/getklse_index_v1.php` | `idx_type=index&region=index&location=&req_date=YYYY-MM-DD` |
| 3 | 热门股 | `http://freeinfo.my/api/klse/getklse_hotstk_v1.php` | `day=1&Lang=1&req_date=YYYY-MM-DD` |
| 4 | 新闻(个股) | `http://www.freeinfo.my/api/klse/getklsenews_bycode_v2.php` | `StkCode=<code>&PostId=&Cat=&Lang=1&keywId=<id>&req_date=YYYY-MM-DD` |
| 5 | 社媒讨论 | `http://freeinfo.my/api/klse/getklse_social_v1.php` | `StkCode=&PostId=&Cat=&Lang=1&req_date=YYYY-MM-DD` |
| 6 | 话题 | `http://www.freeinfo.my/api/klse/getklse_topic_v1.php` | `StkCode=&PostId=&Cat=&Lang=1&req_date=YYYY-MM-DD` |
| 7 | 股息 | `http://www.freeinfo.my/api/klse/getklsediv_bycode_v1.php` | `StkCode=<code>&req_date=YYYY-MM-DD` |
| 8 | 业绩展望 | `http://www.freeinfo.my/api/klse/getklse_prospect_v1.php` | `req_date=YYYY-MM-DD` |
| 9 | 业绩(个股) | `http://www.freeinfo.my/api/klse/getklseprospect_bycode_v1.php` | `stk_code=<code>&q_year=&PostId=&KeywId=&req_date=YYYY-MM-DD&os=and` |
| 10 | **选股** | `http://www.klsestock.com/json_filter_v1.php` | `id=20&bo=&yh=&tp=&gw=&nc=&iw=&day=&type=&trend=&pri_mi=&pri_mx=&sector=&ver=3.7.1&sn=own` |
| 11 | 图表-ADAM | `http://www.stockhunter.my/api/klse/get_chart_adam.php` | `StkCode=<code>&req_date=YYYY-MM-DD` |
| 12 | 图表-动量板块 | `http://www.stockhunter.my/api/klse/get_chart_mom_subsector.php` | `req_date=YYYY-MM-DD` |
| 13 | 图表-Happy/Panic | `http://www.freeinfo.my/api/klse/get_chart_happypanic.php` | `req_date=YYYY-MM-DD` |
| 14 | 版本检查 | `http://freeinfo.my/api/klse/check_app_ver.php` | `AppVersion=3.7.1&req_date=YYYY-MM-DD` |
| 15 | 自选(gold) | `http://freeinfo.my/api/klse/get_goldplus_watchlist_v1.php` | `req_date=YYYY-MM-DD` |
| 16 | 板块JSON | `http://klsegroup.com/json_cache_v1.php` | `id=2&sector=<sector>` (明文, 无加密) |
| 17 | AI-ADAM | `http://klsechart.my/ai/ai_adam.php` | `code=<code>` (明文) |

### ⚠️ 参数坑（实测踩过）
- **`Lang` 不是 `en`**！取值：`1`=英文, `2`=中文, `""`=都含。用 `en` 服务端返回空。
- **news 必带 `keywId`**：个股详情传股票 code；全局新闻传空 `keywId=` 也返回数据。
- **screener 的 `sn`**：源码用 `Build.SERIAL`，实测 `own` 即可。

---

## 2. App 截图功能 ↔ 接口映射

基于用户 18 张实机截图还原：

| App 页面 | 截图证据 | 底层接口 |
|---|---|---|
| 个股详情 (MAXIS 6015) | 价/涨跌/Bid-Ask/年高年低/200-20ma/量 | `getcurresult_v1` 或 个股详情 |
| WARRANT 标签 | 权证列表 | (待挖, 疑似 `getcurresult` is_w=1 或专用) |
| FUNDAMENTAL 标签 | PE/ProfitMargin/EV-EBIT/DebtToCash/CurrentRatio/EarningYield/ROE/DY/DPS/NTA/PB/DebtToEquity/Cash | screener 106字段 / 财务接口 |
| TECHNICAL 标签 | MACD/RSI/OBV/Bollinger | screener 106字段 |
| Q-RESULT 标签 | 净利柱+利润率线组合图 | `getklseprospect_bycode_v1.php` |
| NOTES 标签 | ADD NOTE | 本地存储(无API) |
| NEWS 标签 | MAXIS 股息新闻流 | `getklsediv_bycode_v1` / `getklsenews_bycode_v2` |
| DIVIDEND 标签 | MAXIS 4条股息 DPS=4.000 | `getklsediv_bycode_v1.php` ✅实测 |
| Indices 页 | HANG SENG/CSI300/STI | `getklse_index_v1.php` region=ASIA/WORLD |
| Overview (Malaysia) | 涨跌家数/星级分布/板块统计 | `get_chart_happypanic.php`(聚合图) |
| Hot Stock | DAY/WEEK/MONTH 榜单 | `getklse_hotstk_v1.php` day=1/7/30 ✅实测 |
| Top Volume/Gainer/Loser | 列表 | Overview 子类 |
| Hunt 筛选 SA/FA/TA/CA | 4标签+条件 | `json_filter_v1.php` (screener) |
| Candle Analysis (CA) | 19种K线形态 | screener `candle_*` 字段 |
| Economic News | LOCAL/WORLD/SOCIAL/TOPIC | `getklsenews_bycode_v2` / `getklse_topic_v1` ✅实测 |

---

## 3. 实测验证（2026-08-14，经 CORS 代理）

| 接口 | 结果 | 样本 |
|---|---|---|
| screener | ✅ | AHB/7315 等 4 只, 106字段 |
| news(bycode) | ✅ | AHB削资3700万 / CelcomDigi派息3.4仙 |
| social | ✅ | 9shares / The Storm Media 等源 |
| hotstock | ✅ | GAMUDA[22] MAYBANK[19] 等 |
| dividend | ⚠️ 空 | 需传真实 StkCode(MAXIS截图证明有数据, 接口存活) |
| checkver | ✅ | app_version=3.7.1, server_date=2026-08-14 |
| curresult/index/prospect | ⚠️ 空 | 可能走个股详情专用接口(截图数据来自别处) |

> dividend 空的原因：可能 `StkCode` 需 URL 编码或该接口对部分股无记录；MAXIS 截图证明其返回真实股息数据，接口本身存活。

---

## 4. 待挖接口（截图有但 dex 未明确定位）

- **Warrant 列表**：截图有 WARRANT 标签，dex 未直接找到 warrant 专属 endpoint
- **个股详情完整接口**：MAXIS 的 FUNDAMENTAL/TECHNICAL 数据可能来自 screener 单只查询或另一个 `getstockinfo` 类接口
- **Overview 聚合统计**：涨跌家数/星级分布，疑似 `get_chart_happypanic.php` 返回数据内解析

---

*文档版本：2026-08-14 · 参数逐字来自 dex 源码 + 实机截图核对 · 加密方式字节级确认*
