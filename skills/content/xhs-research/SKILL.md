---
name: xhs-research
description: 用 TikHub 小红书 MCP（tikhub-xhs）做选题调研和对标账号分析。当用户说找选题、选题灵感、什么内容在火、关键词热度/蓝海词/扩词、分析对标账号/竞品博主、拆解某个博主或某篇爆款笔记、找相似博主时使用。给出关键词、赛道、博主主页链接/昵称/小红书号或笔记链接都适用。
---

# 小红书选题 & 对标账号分析

数据来自 MCP 服务 `tikhub-xhs`，工具名都带 `mcp__tikhub-xhs__` 前缀（下文省略）。工具是延迟加载的，用前先用 ToolSearch `select:` 一次性加载本流程要用的全部工具。

## 计费纪律（先读）

- **每次调用都扣费**，HTTP 200 即使返回空数据也扣。拿到空结果**不要原样重试**，换参数或跳过。
- 先少量取样，确认方向再扩大；每个流程默认预算 ≈ 15 次调用，超过前先和用户确认。
- 同一会话里已经拿到的数据直接复用，不重复请求。
- `pgy_*` 接口的业务数据在 `data.data` 里（两层信封）。
- 关联词里 `brandTag=2` 的品牌词数据全为 0，是平台屏蔽，不是没热度，忽略即可。

## 流程 A：找选题

输入：一个核心词或赛道（如「AI工具」）。

1. **扩词** `xiaohongshu_pgy_get_keyword_related(search_word)` → `upSearchWords`（搜这个词之前搜的）+ `downSearchWords`（之后搜的），每个词自带 `searchScore` 搜索指数、`noteNum` 笔记数、`readTotalCount` 阅读量。
2. **算机会分**：对 searchScore>0 的词计算 `供需比 = searchScore / noteNum`。高搜索 + 低笔记数 = 蓝海词。按供需比排序，同时排除和用户赛道明显无关的词（关联词里常混入噪音，如「美股」「磨豆机」）。
3. **挑 3–5 个候选词深挖**（按需，别全调）：
   - `xiaohongshu_pgy_get_keyword_stat(search_word)` → 30 日环比（`*30bm` 字段）+ 发这个词的博主画像（类目、人设占比）。
   - `xiaohongshu_pgy_get_keyword_daily(search_word)` → 逐日走势，判断是在涨还是在退。
4. **看爆款长什么样**：`xiaohongshu_app_v2_search_notes(keyword, sort_type="popularity_descending", time_filter="半年内")` 取 1 页，看高赞笔记的标题、封面形式、图文/视频。
   - `sort_type`：`general` / `time_descending` / `popularity_descending`(点赞) / `comment_descending` / `collect_descending`(收藏，干货类更有参考意义)
   - `note_type`：`不限` / `视频笔记` / `普通笔记`(图文)；`time_filter`：`不限` / `一天内` / `一周内` / `半年内`
   - 翻页要带首页返回的 `search_id` 和 `search_session_id`。
5. **可选 · 看大盘在火什么**：`xiaohongshu_pgy_get_content_square(biz_type=1, search_word=核心词, date_range=7, order_by="premium_engage_rate")`
   - `biz_type=1` 是全平台热门榜，可加 `category="内容类目#科技数码"` 这类筛选（类目：美妆、护肤、母婴、时尚、美食、家居家装、运动健身、宠物、教育、职场、情感、科技数码、出行旅游、健康养生、商业财经、生活记录等）。
   - `date_range` 只能 3/7/14/30；`page_size` 最大 34，榜单固定 Top100。
   - **不要传该榜不支持的字段，也不要把不用的字段传成空串或 0**，会 422 或被当成真实筛选。
6. **可选 · 平台热点**：`xiaohongshu_app_v2_get_creator_hot_inspiration_feed()` 看官方推给创作者的热点灵感。

**输出**：一张候选词表（词 / 搜索指数 / 笔记数 / 供需比 / 30日趋势），然后给 3–5 个具体选题，每个写清：标题方向、切入角度、参考爆款（附链接和数据）、为什么现在做。

## 流程 B：对标账号分析

输入：博主主页链接、分享文案、昵称或小红书号。

1. **拿到 user_id**
   - 有链接/分享文案：`xiaohongshu_app_v2_get_user_info(share_text=...)`，返回里有 user_id。
   - 只有昵称：`xiaohongshu_app_v2_search_users(keyword=昵称)`，让用户确认是哪一个。
2. **基础盘**：`xiaohongshu_app_v2_get_user_info(user_id)` → 粉丝、获赞与收藏、简介、笔记数。
3. **近期内容**：`xiaohongshu_app_v2_get_user_posted_notes(user_id)`，用 `cursor` 翻页，一般 2–3 页（约 30–60 篇）就够。统计：发布频率、图文/视频占比、点赞分布，找出**爆款（点赞 ≥ 该号中位数 3 倍）**。
4. **拆爆款**（挑 2–3 篇）：`xiaohongshu_app_v2_get_image_note_detail(note_id)` 或 `..._get_video_note_detail`，看正文结构和标签；`xiaohongshu_app_v2_get_note_comments(note_id)` 看评论区高频问题 = 下一篇选题线索。
5. **商业数据**（仅蒲公英入驻博主有；拿不到就跳过，不重试）：
   - `xiaohongshu_pgy_get_blogger_data_summary(user_id)` → 报价/CPM 预估、粉丝增长及同行百分位
   - `xiaohongshu_pgy_get_blogger_fans_profile(user_id)` → 粉丝性别、年龄、地域、兴趣
6. **扩对标**：`xiaohongshu_pgy_get_blogger_similar(user_id, page_size=4)` 找相似博主，列给用户挑，不自动逐个深挖。

**输出**：账号定位一句话 → 数据概览表 → 内容结构（栏目/选题类型占比）→ 爆款拆解（标题公式、封面、结构、为什么火）→ 可以直接借鉴的 3 点 + 用户可以做出差异的 2 点 → 相似博主清单。

## 通用

- 笔记链接：`https://www.xiaohongshu.com/explore/{note_id}`；用户主页：`https://www.xiaohongshu.com/user/profile/{user_id}`。
- 报告用中文写，数字给出处（哪条笔记、哪个接口）。用户要存档时，写到当前目录的 `reports/YYYY-MM-DD-<主题>.md`。
- 结论要落到「下一篇写什么」，不要只罗列数据。
