# StockHunter API 合约（传什么 / 返什么）

逆向来源：StockHunter Malaysia 3.7.1 APK（jadx 反编译）+ Python 直连实测。
**加密统一**：AES-256-CBC，key=`Kls3@p#GI3ch!qEh`，iv=16×0x00，PKCS5Padding，Base64。
**`req_date` 必须传明天**（本机今天+1天），今天/过去均拒（news 报 Invalid access token、index 报 Invalid token）。

---

## 一、GET 接口（参数拼 URL `?hash=<AES>&os=and`）

### 1. news（个股/全局新闻）
- URL: `http://www.freeinfo.my/api/klse/getklsenews_bycode_v2.php`
- 传: `StkCode=<空|代码>&PostId=&Cat=&Lang=1|2&keywId=<空|代码>&req_date=明天`
- 返: `{is_success, result_value:[{title,date,source,summary}]}` ✅10条

### 2. social（社媒）
- URL: `http://freeinfo.my/api/klse/getklse_social_v1.php`
- 传: `StkCode=&PostId=&Cat=&Lang=1&req_date=明天`
- 返: `{is_success, result_value:[]}` ✅5条

### 3. hotstock（热门）
- URL: `http://freeinfo.my/api/klse/getklse_hotstk_v1.php`
- 传: `day=1|7|30&Lang=1&req_date=明天`
- 返: **裸数组**[{stk_code,stk_name,...}] ✅3730字节

### 4. index（指数）
- URL: `http://www.freeinfo.my/api/klse/getklse_index_v1.php`
- 传: `idx_type=index&region=ASIA|ASEAN|WORLD|MALAYSIA&location=&req_date=明天`
- 返: `{is_success, result_value:[{name,point,chg,chg_pct}]}` ✅4条

### 5. screener（选股/个股宽表）
- URL: `http://www.klsestock.com/json_filter_v1.php`
- 传: `id=20&<SA/FA/TA/CA筛选>&ver=3.7.1&sn=own`
- 返: **裸数组**1096只×106字段 ✅2.2MB

### 6. curresult（实时报价——空）
- URL: `http://freeinfo.my/api/klse/getcurresult_v1.php`
- 传: `req_date=明天`
- 返: `{is_success, result_value:[]}` ⚠️0条（报价改从 screener.price）

---

## 二、json_cache 系列（GET，AES 加密 `id=N` 放 hash）

> ⚠️ 关键：之前误用明文 `?id=N` 返 `{"OS":"NA"}`。正确是 **AES("id=N") 放 `?hash=`**。
> base: `http://www.klsestock.com/json_cache_v1.php` 或 `json_cache_v2.php`
> 构造: `?hash=<AES("id=N")>&os=and`

| id | 文件 | 内容 | 返 |
|---|---|---|---|
| 1 | v1 | Overview 市场概览 | [{sector,s_up,s_down,s_npc,...}] ✅ |
| 2 | v1 | Watchlist 自选（需登录） | ⚠️空 |
| 6 | v1 | Trend 星级榜单 | [{tid,stockname,...}] ✅47万字节 |
| 8 | v1 | StockInfo Technical 技术 | ⚠️空(raw[0]) |
| 9 | v1 | HotList Week 周热门 | [{tid,...}] ✅ |
| 10 | v1 | HotList Month 月热门 | ✅ |
| 11 | v1 | Growth ConQ 连续季增 | ✅ |
| 12 | v1 | Growth YoY | ✅ |
| 13 | v1 | Growth QoQ | ✅ |
| 16 | v1 | Report 季报报告 | ✅2.2MB |
| 17 | v1 | TopProfit 最高盈利 | ✅ |
| 18 | v1 | NetCash 净现金最高 | ✅ |
| 19 | v1 | DividendYield 股息率 | ✅ |
| 22 | v1 | Toploss 最大亏损 | ✅ |
| 23 | v1 | Shariah 伊斯兰合规 | ✅ |
| 3 | v2 | HotList 热门 | ✅ |
| 26 | v2 | TopGainer 涨幅榜 | [{tid,stockname,stockcode,...}] ✅ |
| 27 | v2 | TopLoser 跌幅榜 | ✅ |
| 28 | v2 | TopGain% 涨幅% | ✅ |
| 29 | v2 | TopLose% 跌幅% | ✅ |
| 30 | v2 | Momentum VolumeUp 量增 | ✅ |
| 31 | v2 | Momentum GapUp 跳空 | ✅ |
| 32 | v2 | Momentum TurnOver 换手 | ✅ |
| 33 | v2 | SectorList 板块列表 | [{sector,...}] ✅ |
| 34 | v2 | SectorDetails 板块详情 | ✅2MB |
| 35 | v2 | DividendPolicy 股息政策 | ⚠️空 |
| 37 | v2 | LatestQ 最新季报 | ✅ |
| 38 | v2 | Warrant 个股权证 | ⚠️`{sector:NA}`（数据源空，接口活）|
| 39 | v2 | WarrantDiscount 折价权证 | [{code,pri_open,...}] ✅ |
| 40 | v2 | WarrantTopVolume 高量权证 | ✅ |
| 41 | v2 | WarrantHighTurnOver 高换权证 | ✅ |
| 43 | v2 | TopRevenue 最高营收 | ✅ |

---

## 三、POST 接口（body 放 hash，Volley getParams）

### 7. DIVIDEND（股息）
- URL: `http://www.freeinfo.my/api/klse/getklsediv_bycode_v1.php`
- 方法: POST  body: `hash=<AES("StkCode=<代码>&req_date=明天")>&os=and`
- 返: `{is_success, result_value:[{id,r_date,f_year,ex_date,pay_date,en_date,en_type,div_cent,stk_list}]}` ✅直连通

### 8. Q-RESULT（季报）
- URL: `http://www.freeinfo.my/api/klse/getklseprospect_bycode_v1.php`
- 方法: POST  body: `hash=<AES("stk_code=<代码>&q_year=<当年>&PostId=&KeywId=&req_date=明天")>&os=and`
- 返: `{is_success:false, err_msg:No data}` ⚠️接口活但当前无数据（App 缓存）

### 9. prospect_v1（主题新闻用）
- URL: `http://www.freeinfo.my/api/klse/getklse_prospect_v1.php`
- 方法: POST  body: `hash=<AES("stk_code=<代码>&q_year=<当年>&PostId=&KeywId=&req_date=明天")>&os=and`
- 返: `998 No data` ⚠️

---

## 四、图表接口（GET，返 HTML/JS 图表）

- ADAM: `http://www.stockhunter.my/api/klse/get_chart_adam.php?StkCode=<代码>&req_date=明天`
- Momentum: `http://www.stockhunter.my/api/klse/get_chart_mom_subsector.php?req_date=明天`
- HappyPanic: `http://www.freeinfo.my/api/klse/get_chart_happypanic.php?req_date=明天`
- 互动图: `http://www.stockhunter.my/tv_v6/chart.php?...`
- AI-ADAM: `http://klsechart.my/ai/ai_adam.php?...`

---

## 五、其他（注册/版本）

- regusr: `https://stockhunter.my/api/klse/regusr.php` GET（返回 err_msg 1011，参数未完全逆向）
- check_app_ver: `http://freeinfo.my/api/klse/check_app_ver.php` GET
- news topic: `http://freeinfo.my/api/klse/getklse_topic_v1.php` GET
- news bycodelist: `http://freeinfo.my/api/klse/getklsenews_bycodelist_v1.php` GET
- stkchat: `http://freeinfo.my/api/klse/getklse_stkchat_v1.php` GET

---

## 六、总结（直连实测）

| 类别 | 状态 |
|---|---|
| news/social/hotstock/index/screener | ✅ 全活（GET+AES） |
| json_cache v1/v2（Overview/TopGainer/Loser/Trend/Growth/TopProfit/NetCash/Toploss/Shariah/HotList/Momentum/Sector/Warrant系列/LatestQ/TopRevenue） | ✅ 全活（GET+AES id=N） |
| dividend | ✅ 活（POST+AES body） |
| qresult/prospect_v1 | ⚠️ 接口活但无数据 |
| warrant id=38 | ⚠️ 接口活但数据源空 |
| curresult/tech id=8/watchlist id=2 | ⚠️ 空（需登录或下线） |
| klsegroup.com 系列 | ❌ DNS 死（get_json.php 等全 11001） |

**本会话关键修正**：
1. `req_date` 传明天（服务端时区偏移校验）
2. json_cache 用 **AES("id=N")** 不是明文 `?id=N`（之前误用明文返 OS:NA 判死，实测 AES 全活）
3. dividend/qresult 是 **POST**（body hash），直连通；经 Cloudflare Worker 代理 POST 被吞（代理只转发 GET）
4. warrant id=38 是 GET+AES（非 POST），但数据源返回空
