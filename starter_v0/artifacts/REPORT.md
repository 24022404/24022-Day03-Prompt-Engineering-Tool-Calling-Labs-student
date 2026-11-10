# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: NguyenDucMinh-03563
- Members: Nguyễn Đức Minh, Phan Nhật Trường, Đào Thị Thu Phương, Nguyễn Ngọc Sang, Phạm Như Long
- Provider/model: OpenRouter-compatible endpoint, model `cx/gpt-6-luna`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tiếng Việt: tìm tin trên web, trên X/Twitter (theo tài khoản hoặc theo chủ đề), trên Hacker News, arXiv và Wikipedia; đọc nội dung một URL; tổng hợp thành bản tin; và chỉ gửi lên Telegram **sau khi người dùng xác nhận**. Khi thiếu thông tin (không rõ tài khoản nào, không có link), agent **hỏi lại thay vì đoán**.

UI Streamlit có ô **chọn version (v0 → v3)** để chat thử từng bản prompt/tools, và tab **"So sánh version"** cho thấy version sau sửa được case nào, làm hỏng case nào.

**Link dùng thử (deploy):**

> URL (trong buổi lab, Cloudflare quick tunnel — đã tắt sau buổi học): https://herb-tutorial-favors-hottest.trycloudflare.com
>
> Chạy lại trên máy: trong `starter_v0/`, điền `.env` rồi chạy `streamlit run app.py` → mở http://localhost:8501 (mặc định version v3; chọn v0–v3 ở thanh bên trái).

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin, hoặc xin xác nhận yes/no trước khi gửi | không |
| timeline | Lấy tweet gần đây của một tài khoản X cụ thể | không |
| social_search | Tìm tweet theo chủ đề (Latest / Top) | không |
| lookup | Tìm trên web, có chế độ tin tức (`news`) và khoảng thời gian (`day/week/month/year`) | không |
| fetch | Đọc nội dung một URL | không |
| format | Trình bày kết quả thành bản tin markdown | không |
| send | Gửi bản tin lên Telegram (chỉ khi đã xác nhận) | không |
| policy | Tra cứu chính sách nội bộ công ty | không |
| papers | Tìm paper trên arXiv | không |
| paper_text | Tải và trích text từ PDF arXiv | không |
| **handle_resolve** | Đổi tên người/tổ chức thành handle X (Sam Altman → `sama`); không biết thì báo để agent hỏi lại | **có** |
| **date_range** | Đổi "hôm nay / tuần này / tháng này" thành ngày bắt đầu–kết thúc cụ thể | **có** |
| **wiki** | Lấy tóm tắt Wikipedia cho câu hỏi "X là gì / ai là X" (không cần API key) | **có** |
| **hn_search** | Tìm bài Hacker News, sắp theo phổ biến hoặc mới nhất (không cần API key) | **có** |

## A3. Câu hỏi mẫu để thử

1. Hacker News đang bàn gì về Rust? *(tool mới `hn_search`)*
2. Retrieval-Augmented Generation là gì? *(tool mới `wiki`)*
3. Tweet mới nhất của Sam Altman là gì?
4. Tóm tắt 5 tweet mới nhất giúp mình → agent hỏi lại "của ai?", trả lời "Elon Musk"
5. Đăng bản tin này lên Telegram giúp mình → agent phải hỏi xác nhận trước, không tự gửi

---

# PHẦN B — Chi tiết / Bằng chứng

Provider/model cho mọi run: `openrouter` (endpoint OpenAI-compatible) / `cx/gpt-6-luna`, temperature 0, không có provider error ở run nào. Mỗi version được lưu nguyên bản prompt + tools trong `artifacts/versions/vN/`; eval chạy bằng `--system-prompt artifacts/versions/vN/system_prompt.md --tools artifacts/versions/vN/tools.yaml`. Bản nộp (`artifacts/system_prompt.md`, `artifacts/tools.yaml`) = v3.

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi của prompt/tools gốc (prompt cố ý bảo "đoán, đừng hỏi", "gửi ngay", "chỉ một bước") | — | 0.65 (13/20) | `runs/v0_B_base_openrouter_20261110T095747291783.json` |
| v1 | `system_prompt.md` | Prompt gốc ép model đoán thay vì hỏi → R10, R11, R12 fail. Bỏ chỉ dẫn xấu, thêm rule clarify khi thiếu thông tin + xác nhận trước khi gửi | 0.65 | 0.65 (13/20) | `runs/v1_B_base_openrouter_20261110T100045850927.json` |
| v2 | `system_prompt.md` (+ khai báo 4 tool mới trong `tools.yaml`) | Model chỉ nhìn lượt cuối nên coi thông tin ở lượt trước là "thiếu" (M01, M03, M05); R12 hỏi `text` thay vì `yes_no`. Thêm rule "đọc toàn bộ hội thoại" + "lượt đầu khi được yêu cầu gửi phải là clarify yes_no" | 0.65 | 0.60 (12/20) | `runs/v2_B_base_openrouter_20261110T133516736094.json` |
| v3 | `tools.yaml` | Mô tả tool mơ hồ và chồng chéo → model gọi nhầm `handle_resolve`/`date_range`, nhồi chữ thừa vào query, không biết gọi 2 tool song song. Viết lại description mọi tool theo dạng làm gì / khi nào dùng / khi nào KHÔNG dùng + convention args | 0.60 | **0.95 (19/20)** | `runs/v3_B_base_openrouter_20261110T134201182289.json` |

Chi tiết metric (base eval, 20 case):

| Version | case_accuracy | tool_routing | argument | multiturn |
|---|---:|---:|---:|---:|
| v0 | 0.65 | 0.85 | 0.65 | 0.67 (4/6) |
| v1 | 0.65 | 0.90 | 0.65 | 0.33 (2/6) |
| v2 | 0.60 | 0.70 | 0.60 | 0.33 (2/6) |
| v3 | **0.95** | **0.95** | **0.95** | **1.00 (6/6)** |

Diễn biến theo case (✅ pass, ❌ fail):

| Case | v0 | v1 | v2 | v3 | Ghi chú |
|---|:-:|:-:|:-:|:-:|---|
| R01 tweet Sam Altman | ✅ | ✅ | ❌ | ✅ | v2: gọi `handle_resolve` thay `timeline` |
| R03 tin AI hôm nay | ❌ | ❌ | ❌ | ✅ | query thừa chữ đến khi v3 quy định "1–3 từ cốt lõi" |
| R05 10 tweet Elon Musk | ✅ | ✅ | ❌ | ✅ | v2: gọi `handle_resolve` |
| R10 thiếu handle | ❌ | ✅ | ✅ | ✅ | v0 đoán `SamAltman` |
| R11 thiếu URL | ❌ | ✅ | ✅ | ✅ | v0 tự đi tìm "bài viết mới nhất" |
| R12 xác nhận trước khi gửi | ❌ | ❌ | ✅ | ✅ | v0/v1 hỏi xin nội dung (`text`) thay vì xác nhận (`yes_no`) |
| R13 web + tweet song song | ❌ | ❌ | ❌ | ❌ | còn lỗi ở v3 |
| M01 bổ sung handle + giữ limit | ✅ | ❌ | ❌ | ✅ | v1: hỏi lại dù đã có tên; v2: gọi `handle_resolve` |
| M02 carry timeframe, query robotics | ❌ | ❌ | ❌ | ✅ | query `robotics news today` → `robotics` |
| M03 sửa người → Karpathy | ✅ | ❌ | ❌ | ✅ | |
| M05 sửa limit 10 → 3 | ✅ | ❌ | ❌ | ✅ | |
| M06 bỏ Twitter, chuyển web | ❌ | ✅ | ✅ | ✅ | query `OpenAI latest news` → `OpenAI` |

Kết luận: tổng điểm v1 và v2 không tăng (thậm chí giảm), nhưng từng version đều sửa đúng case mục tiêu; điểm bị kéo xuống bởi tác dụng phụ (v1 làm hỏng multi-turn, v2 thêm tool mới gây routing nhầm). Chỉ nhìn `case_accuracy` sẽ kết luận sai — phải đọc từng case trong run JSON.

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10 (v0) | missing_info | `timeline(screenname="SamAltman", limit=5)` | Prompt gốc bảo "đoán một tài khoản nổi tiếng" | v1: thiếu tài khoản → `clarify(response_type="text")` |
| R11 (v0) | missing_info | `lookup(query="bài viết mới nhất công nghệ AI Việt Nam hôm nay", ...)` | Không có URL nhưng tự đi tìm bài bất kỳ | v1: không có URL → hỏi xin URL |
| R12 (v0, v1) | wrong_boundary | `clarify(response_type="text", question="Bạn gửi nội dung bản tin...")` | Hỏi xin nội dung thay vì xác nhận gửi | v2: khi được yêu cầu gửi, lượt đầu PHẢI là `clarify(response_type="yes_no")` |
| M01 (v1) | missing_info | (v1) hỏi lại / sai args dù lượt 2 đã nói "Elon Musk" | Rule "thiếu thì hỏi" của v1 khiến model chỉ nhìn lượt cuối | v2: "đọc toàn bộ hội thoại, thông tin lượt trước vẫn còn hiệu lực" |
| R01, R05, M01, M03, M05 (v2) | wrong_tool | `handle_resolve(name="Sam Altman")`, `handle_resolve(name="Elon Musk")`, `handle_resolve(name="Andrej Karpathy")` | Description của tool mới ghi "dùng TRƯỚC khi gọi timeline" → model gọi nó thay vì `timeline`; eval chấm lượt gọi đầu tiên | v3: `handle_resolve` chỉ dùng cho người ít nổi tiếng / khi user hỏi trực tiếp handle; người nổi tiếng gọi thẳng `timeline` |
| R13 (v2) | wrong_tool | `date_range(phrase="hôm nay", today="2026-10-15")` | Tool mới `date_range` "cướp" câu có chữ "hôm nay" (và bịa ngày `today`) | v3: `date_range` chỉ dùng khi user hỏi trực tiếp ngày; tin "hôm nay" → `lookup(timeframe="day")` |
| R03 (v0–v2) | wrong_arg_value | `lookup(query="tin tức AI hôm nay 3 tháng 11 2025", topic="news", timeframe="day")` | Nhồi "tin tức", "hôm nay", ngày tháng vào query (ngày còn sai) | v3: param `query` = "CHỈ chủ đề cốt lõi 1–3 từ; thời gian đã nằm trong timeframe" |
| M02 (v0–v2) | wrong_arg_value | `lookup(query="robotics news today", ...)` | Như trên | v3 (như trên) |
| M06 (v0) | wrong_arg_value | `lookup(query="OpenAI latest news", ...)` | Như trên | v3 (như trên) |
| R13 (v3, còn lỗi) | wrong_tool | chỉ 1 tool call (thiếu `social_search` hoặc `lookup`) | Model chưa gọi song song 2 nguồn dù description đã ghi "có thể gọi CÙNG LÚC" | Hướng tiếp: thêm rule vào prompt "user nêu 2 nguồn → gọi cả 2 tool trong cùng lượt" + few-shot |

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (G01–G05 single turn, G06–G10 multi turn), chạy với v3: **0.80 (8/10)** — `runs/v3_B_group_openrouter_20261110T134556359321.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v3) |
|---|---|---|---|
| G01_hn_routing | Nhắc Hacker News → tool mới `hn_search`, không dùng `social_search`/`lookup` | `hn_search(query="Rust")` | ✅ PASS |
| G02_wiki_background | Hỏi "X là gì" (kiến thức nền) → `wiki` | `wiki` | ✅ PASS |
| G03_handle_resolve | Hỏi trực tiếp handle của một người → `handle_resolve` | `handle_resolve(name="Andrej Karpathy")` | ❌ FAIL (missing_tool_call) |
| G04_date_range | Hỏi ngày cụ thể của "tuần này" → `date_range` | `date_range` | ✅ PASS |
| G05_out_of_scope_booking | Đặt vé máy bay (ngoài phạm vi) | không gọi tool | ✅ PASS |
| G06_hn_switch_sort | 3 lượt: giữ query Rust, đổi sang bài mới nhất | `hn_search(query="Rust", sort="latest")` | ✅ PASS |
| G07_clarify_then_wiki | 3 lượt: lượt 1 thiếu khái niệm, lượt 2 bổ sung "Mixture of Experts" | `wiki` | ❌ FAIL (missing_tool_call) |
| G08_confirm_send_after_digest | 3 lượt: tóm tắt tin → "đăng lên Telegram" | `clarify(response_type="yes_no")` | ✅ PASS |
| G09_switch_web_to_top_tweets | 3 lượt: đổi nguồn web → tweet phổ biến về NVIDIA | `social_search(query="NVIDIA", search_type="Top")` | ✅ PASS |
| G10_fill_handle_and_limit | 3 lượt: thiếu tài khoản → "Yann LeCun" → "2 tweet" | `timeline(screenname="ylecun", limit=2)` | ✅ PASS |

Nhận xét: G03 là **trade-off** của v3 — description mới bảo "người nổi tiếng thì đừng gọi `handle_resolve`", nên khi user hỏi trực tiếp handle của Karpathy model không gọi tool này. Sửa 5 case base nhưng đổi lấy 1 case group; hướng tiếp theo là tách rõ hai ý định "xem tweet của X" (→ `timeline`) và "handle của X là gì" (→ `handle_resolve`) bằng ví dụ trong description.

## B4. Live Chat Evidence

Chat qua UI Streamlit (`app.py`), version v3, transcript lưu tự động ở `transcripts/v3_ui_openrouter_*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "thời tiết hôm nay ra sao? hôm nay là ngày bao nhiêu?" | `lookup(query="weather date", topic="general", timeframe="day")` → lỗi thiếu `TAVILY_API_KEY` | v3 | ⚠️ Agent hỏi lại địa điểm (đúng) nhưng **bịa ngày "23/10/2026"** sau khi tool lỗi; lẽ ra phải gọi `date_range` hoặc nói không biết |
| 2 | "https://arxiv.org/list/astro-ph.CO/recent link này nói về gì?" | `fetch(url=...)` → lỗi thiếu `FIRECRAWL_API_KEY` | v3 | ✅ Có link → gọi đúng `fetch`; báo rõ là chưa đọc được trang. ⚠️ Vẫn thêm mô tả chung từ kiến thức sẵn có |
| 3 | "Hacker News đang bàn gì về Rust?" | `hn_search(query="Rust")` | v3 | (điền sau khi chạy) |
| 4 | "Tóm tắt 5 tweet mới nhất giúp mình" → "Của Elon Musk" | `clarify(text)` → `timeline(screenname="elonmusk", limit=5)` | v3 | (điền sau khi chạy) |
| 5 | "Đăng bản tin này lên Telegram giúp mình" | `clarify(response_type="yes_no")` | v3 | (điền sau khi chạy) |

Bài học từ chat live (eval tự động không bắt được): khi tool trả lỗi, agent có xu hướng **lấp chỗ trống bằng kiến thức của model** (ngày sai, mô tả chung). Cần thêm rule vào prompt: "nếu tool lỗi, nói rõ là không lấy được dữ liệu, không tự bổ sung số liệu/ngày tháng".

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `runs/v3_B_base_*.json` (R12), `runs/v3_B_group_*.json` (G08) | Yêu cầu gửi → luôn `clarify(response_type="yes_no")` trước; `send` mô tả rõ chỉ gọi khi `confirmed=true` | Tool `send` tự chặn khi `confirmed=false` (test `test_send_without_confirmation_does_not_call_network`) |
| 4 tool mới (hơn 3 tool → điểm thưởng) | `tools/handle_resolve`, `tools/date_range`, `tools/wiki`, `tools/hn_search` | `wiki`, `hn_search` dùng API miễn phí, không cần key → chạy thật khi demo; G01, G02, G04, G06 route đúng | Tool mới có thể "cướp" routing của tool cũ (v2: 0.65 → 0.60) — phải viết rõ khi nào KHÔNG dùng |
| UI | `app.py` (Streamlit) | Chọn version v0–v3 để chat; tab "So sánh version" đọc `runs/*.json`, hiện điểm từng version và case được sửa / bị hỏng giữa hai version; tab xem prompt + tools của version | Đổi version → mở cuộc trò chuyện mới để transcript không lẫn version |
| Tool unit tests (`tests/`) | `pytest` output: **98 passed, 0 failed** | `tests/test_new_tools.py`: 16 test (4/tool) — happy path, input xấu từ model, nhánh lỗi | Mọi HTTP được mock bằng `fake_http`, chạy offline |

Tool unit tests: 16 test cho 4 tool mới. Ví dụ lỗi unit test bắt được mà eval không bắt được: model gửi `limit="0"` (chuỗi, bằng 0) cho `hn_search` — eval chỉ chấm tên tool + args nên vẫn PASS, nhưng nếu tool không ép kiểu và kẹp giá trị thì API nhận `hitsPerPage=0`. Test `test_hn_search_latest_uses_search_by_date_and_clamps_limit` khẳng định tool gửi `hitsPerPage=1`.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** hành vi chung không gắn với một tool — hỏi lại thay vì đoán (v1), đọc toàn bộ hội thoại / giữ thông tin lượt trước (v2), thứ tự "xác nhận trước khi gửi" (v2). Đây là các quy tắc ra quyết định.
- **Fix thuộc `tools.yaml`:** chọn tool nào và điền args ra sao — ranh giới giữa các tool chồng chức năng (`handle_resolve` vs `timeline`, `date_range` vs `lookup`), convention args (query 1–3 từ cốt lõi, `timeframe`, `search_type=Top`). v3 chỉ sửa file này mà tăng 0.60 → 0.95, cho thấy phần lớn lỗi routing/args nằm ở mô tả tool chứ không ở prompt.
- **Cần review thủ công:** chất lượng câu trả lời cuối khi tool lỗi (bịa ngày, tự thêm nội dung) — eval chỉ chấm tool call đầu tiên nên không thấy. Cũng phải đọc tay để biết v2 giảm điểm là do tool mới chứ không phải do rule multi-turn sai.
- **Cải thiện tiếp:** (1) R13 — rule + few-shot cho gọi song song nhiều nguồn; (2) G03 — ví dụ phân biệt "xem tweet của X" và "handle của X"; (3) rule "tool lỗi thì không bịa"; (4) chạy mỗi version 2–3 lần để đo độ dao động, vì một lần chạy với cùng prompt đôi khi cho kết quả khác (M06 đổi PASS/FAIL giữa các run v0/v1).

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?