# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi ban đầu | — | case_accuracy = 0.65 (13/20) | `runs/v0_B_base_openrouter_20261110T095747291783.json` |
| v1 | `artifacts/system_prompt.md` | Quy định thứ tự ưu tiên clarify giúp hỏi đúng kiểu khi thiếu dữ liệu hoặc chưa xác nhận gửi | case_accuracy = 0.65 | case_accuracy = 0.65 (13/20) | `runs/v1_B_base_openrouter_20261110T104133101896.json` |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

### Kết quả vòng v1

- Log gồm baseline và kết quả v1 đã lưu ở `artifacts/version_log_v1.csv`, vì Windows đang chặn ghi `artifacts/version_log.csv`. Cần đồng bộ vào file chính sau khi ứng dụng đang giữ file nhả quyền ghi. Trong bản log mới, nhãn baseline là `v0` theo run JSON; dòng `v1` giữ tên tác giả đã nhập là `Phan Nhat Truong`.
- Provider/model: `openrouter` / `cx/gpt-6-luna`, cùng model và tools hash với baseline được ghi trong version log. Cả hai run đo đủ 20 case, không có provider error.
- Giả thuyết: model cần thứ tự quyết định rõ ràng — yêu cầu xác nhận trước hành động gửi; hỏi dữ liệu còn thiếu; đủ thông tin thì gọi tool đọc mà không hỏi xác nhận thừa.
- Các case mục tiêu `R10_missing_handle`, `R11_missing_url`, `R12_confirm_before_send`: baseline 0/3, v1 3/3.
- `tool_routing_accuracy`: 0.85 → 0.95; `argument_accuracy`: 0.65 → 0.65; `multiturn_accuracy`: 0.6667 (4/6) → 0.1667 (1/6).
- Kết luận: v1 cải thiện hành vi hỏi lại/xác nhận trong ba case mục tiêu, nhưng chưa cải thiện tổng điểm và có hồi quy ở hội thoại nhiều lượt. Một lần chạy chưa đủ để kết luận về độ ổn định.
- Bảy case còn lỗi: `R03`, `R13`, `M01`, `M02`, `M03`, `M05`, `M06`. Lỗi gồm query chứa thêm từ chỉ tin tức/thời gian, truyền tên hiển thị thay vì handle, và thiếu `social_search` khi yêu cầu cả hai nguồn.
- Bản chụp prompt và khai báo tool của run này: `artifacts/versions/v1/system_prompt.md`, `artifacts/versions/v1/tools.yaml`. Run v1 cũ được giữ nguyên; kết quả ở bảng trên trỏ tới run mới theo đúng hash.
- Kiểm tra code: `python -m pytest -q` đạt **62 passed, 17 skipped**. Các test TODO chưa được triển khai trong vòng sửa prompt này.

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

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
