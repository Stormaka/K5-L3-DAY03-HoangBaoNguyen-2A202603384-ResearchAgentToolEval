# Day 03 Lab — Research Agent — Báo cáo v6

Cập nhật 10/11/2026 (Asia/Saigon). Provider/model: OpenRouter / `openai/gpt-4o-mini`.

## Team

| Thành viên | MSSV | Phân công |
|---|---|---|
| Hoàng Bảo Nguyên — nhóm trưởng | 2A202603384 | Prompt, version log, bằng chứng và tích hợp |
| Hoàng Minh Huy | 2A202603495 | Tools, tools.yaml, fallback và unit tests |
| Nguyễn Huy Giang | 2A202603543 | Eval nhóm, UI, transcript và REPORT |

# PHẦN A — Giới thiệu agent

## A1. Phạm vi và link dùng thử

Agent nghiên cứu bằng tiếng Việt: tìm tin tức/paper, đọc URL, tra policy, Wikipedia/Hacker News, lấy ngày giờ và trình bày digest. Agent hỏi lại khi thiếu thông tin; từ chối giải toán, viết code và dịch thuật độc lập ngoài phạm vi. Câu hỏi về khả năng của agent được trả lời trực tiếp.

**URL public của app nộp:** [Mở Research Agent v6](https://karl-evans-tower-matrix.trycloudflare.com).

Bằng chứng: [`public_app_smoke.json`](public_app_smoke.json). Kiểm tra HTTP `/`, `/_stcore/health`, WebSocket và 5 lượt chat qua chính URL public: từ chối toán, Fibonacci, dịch thuật; gọi `now`; yêu cầu Telegram dừng ở `clarify yes_no`. Metadata phiên phải trỏ đúng `starter_v0/app.py` của repo này và hiển thị đúng artifact v6. Đây là kiểm tra giao thức/nội dung, **chưa phải kiểm tra bố cục bằng ảnh trình duyệt**: công cụ điều khiển Chrome đã dừng vì không xác định được URL để kiểm tra quyền truy cập.

URL là Cloudflare Quick Tunnel tạm thời: phải giữ máy, Streamlit ở cổng 8565 và tunnel chạy khi giảng viên mở. Tunnel mới sẽ đổi URL; phải thử lại và cập nhật REPORT. Đây không phải hosting cố định. Xem [tài liệu Cloudflare](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

**Telegram đang tắt trên UI và mọi luồng chạy model.** UI không khai báo `send`; runtime vẫn chặn nếu model cố gọi `send(confirmed=true)`. Chưa nhận bonus gửi thật. Twitter hiện thiếu `RAPIDAPI_KEY`; một số URL trong đề trả HTTP 404. Không tính các lỗi thực thi này thành chức năng chạy thành công.

## A2. Tools

| Tool | Công dụng | Nhóm tự thêm? |
|---|---|---|
| clarify | Hỏi thông tin / yes_no | Không |
| timeline | Tweet của tài khoản; hiện thiếu key | Không |
| social_search | Tweet theo chủ đề; hiện thiếu key | Không |
| lookup | Tìm web/tin tức; Google News RSS fallback cho news khi bật KEYLESS_FALLBACKS | Không |
| fetch | Đọc URL; direct GET fallback khi bật KEYLESS_FALLBACKS | Không |
| format | Trình bày digest từ items | Không |
| send | Transport Telegram giữ cho unit test; bị chặn trong runtime và ẩn khỏi UI | Không; chưa có bonus gửi thật |
| policy | Policy nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Đọc paper arXiv | Không |
| **wiki** | Tóm tắt Wikipedia vi/en | **Có** |
| **hn_search** | Tìm thảo luận Hacker News qua Algolia | **Có** |
| **now** | Ngày giờ hiện tại | **Có** |

Có 13 implementation đăng ký, 12 tool khai báo cho model trên UI. **Ba tool mới đáp ứng phần bắt buộc; chưa đạt bonus “hơn 3 tool”.**

## A3. Câu hỏi mẫu

1. “Tin AI hôm nay có gì nổi bật?”
2. “Sam Altman là ai?”
3. “Cộng đồng Hacker News đang bàn gì về LLM?”
4. “Hôm nay là ngày mấy?”
5. “Tóm tắt bài này giúp mình” → hỏi URL.
6. “Viết hàm Fibonacci” → từ chối, không có code hay lời giải.
7. “Gửi bản tin lên Telegram” → hỏi về bản nháp; gửi đang tắt.

# PHẦN B — Chi tiết và bằng chứng

## B1. Version evidence và ý nghĩa 40/40

Giữ nguyên log gốc trong `runs/`. Hash prompt/tools nằm trong run và `version_log.csv`; snapshot prompt v4/v5/v6 ở `artifacts/versions/`.

| Version | Thay đổi / giả thuyết | Kết quả và giới hạn |
|---|---|---|
| v0 | Starter yêu cầu đoán thông tin, gửi thiếu xác nhận, ép dùng tool | Base 14/20 theo evaluator cũ |
| v1 | Decision rules, routing, mapping tên → handle | Base 17/19; 1 provider timeout; M02/M06 gọi thừa nguồn |
| v2 | Latest-turn exclusivity | Base 20/20; extension 8/10 theo evaluator cũ |
| v3 | Làm rõ tools.yaml/policy_area; thêm wiki/hn_search/now | Base 20/20; extension 9/10 sau thêm tool; group 10/10 theo evaluator cũ |
| v4 | Policy constraint chạy cùng research call | **40/40 chỉ chọn tool/tham số kỳ vọng**; bỏ qua nội dung từ chối; **21/40 case lỗi thực thi** |
| v5 | Từ chối rõ ràng; evaluator kiểm tra text; siết G05; tách execution metrics; tắt send | **39/40**; R08/R14/G05 từ chối đúng; R12 sai `response_type=text`; **12/40 case lỗi thực thi** |
| **v6** | Sửa R12 yes_no; bỏ log emoji có thể làm hỏng lượt tool trên console Windows | **40/40 chọn tool/tham số + hợp đồng nội dung no_tool**; **12/40 case vẫn lỗi thực thi**, không phải 40 chức năng thành công |

Tổng hợp: [`submission_metrics.json`](submission_metrics.json). Phân tích từng case: `starter_v0/analysis_all_runs.csv`.

| Suite v6 | Run file | Chọn tool/tham số + no_tool content | Case có lỗi thực thi |
|---|---|---:|---:|
| Base | `runs/v6_B_base_openrouter_20261110T154548605449.json` | 20/20 | 10/20 |
| Extension | `runs/v6_B_extension_openrouter_20261110T154539371691.json` | 10/10 | 0/10 |
| Group | `runs/v6_B_group_openrouter_20261110T154510485836.json` | 10/10 | 2/10 |

Trong 40 case v6: **36 case gọi tool, 24 case không ghi nhận lỗi tool, 12 case có lỗi tool, 4 case không gọi tool**. Mười case lỗi do thiếu `RAPIDAPI_KEY`; hai case đọc URL lỗi HTTP 404. Không có provider error trong ba run v6. “Không ghi nhận lỗi tool” chưa chứng minh chất lượng câu trả lời cuối hoặc dữ liệu đầy đủ.

Run v5 đo được: `v5_B_base_openrouter_20261110T153751301140.json`, `v5_B_extension_openrouter_20261110T153932831446.json`, `v5_B_group_openrouter_20261110T153920079588.json`. Run `v5_B_base_openrouter_20261110T153106881802.json` bị sandbox chặn mạng: 20 provider error, 0 case đo được; được giữ để minh bạch, không dùng làm số liệu hành vi.

## B2. Lỗi v4 và cách sửa

[`v4_content_execution_audit.json`](v4_content_execution_audit.json) chấm lại **offline** câu trả lời đã lưu, không phải chạy model mới. Áp dụng yêu cầu từ chối nghiêm ngặt được **37/40**: R08 giải tích phân, R14 viết Fibonacci, G05 dịch sang tiếng Pháp. Cả ba không gọi tool nhưng nội dung sai phạm vi. G05 cũ cho phép `refuse_or_answer_directly`; v5 đổi thành `refuse` trong bộ case nhóm. Bộ base được giữ nguyên.

| Lỗi | Sửa | Bằng chứng |
|---|---|---|
| Prompt gộp toán/code/dịch với câu hỏi khả năng | Tách phạm vi; từ chối bằng mẫu cố định, không kèm lời giải/code/bản dịch | R08/R14/G05 v6 và chat public |
| Evaluator chỉ kiểm tra no_tool | Kiểm tra text; từ chối rồi kèm lời giải cũng FAIL; câu hỏi khả năng phải có nội dung | `tests/test_eval_and_delivery.py` |
| Model tự đặt confirmed=true có thể chạy send | `tool_execution.py` chặn trước implementation; agent/chat dùng chung boundary; UI ẩn tool | Tool/provider giả với confirmed=true, kể cả history có “Đồng ý”: không gọi tool gửi |
| V5 R12 dùng response_type=text | V6 ưu tiên clarify yes_no ở yêu cầu gửi đầu tiên; không duyệt nội dung chưa biết | R12 và G10 v6 PASS |
| Print emoji gây UnicodeEncodeError trên Windows | Bỏ print args/emoji; debug log tên tool | Test console ASCII; public smoke gọi now |

Evaluator dùng **mẫu từ chối cố định**, chuẩn hóa khoảng trắng. Đây là kiểm tra bảo thủ, không phải bộ chấm ngữ nghĩa tổng quát: cách diễn đạt khác cần xem tay. `answer_without_tool` chỉ kiểm tra có nội dung và không trả mẫu từ chối. Case research vẫn chấm tool/subset tham số kỳ vọng, chưa chấm toàn bộ câu trả lời cuối. [`v6_content_execution_audit.json`](v6_content_execution_audit.json) tách lỗi thực thi. Audit ghi hash nguồn/evaluator để đối chiếu.

## B3. Eval nhóm

`data/eval_group.json`: 10 case, 5 single-turn và 5 multi-turn; đều PASS ở v6 theo phạm vi đo ở B1.

| Case | Kiểm tra |
|---|---|
| G01 | Câu hỏi nền → wiki |
| G02 | Hacker News → hn_search |
| G03 | Ngày giờ hiện tại → now |
| G04 | Handle karpathy, limit=7; thực thi vẫn thiếu key |
| G05 | Dịch thuật ngoài phạm vi → từ chối, không dịch |
| G06 | Giữ VinUni, chuyển sang tin hôm nay |
| G07 | Thu hẹp nguồn về Hacker News, giữ chủ đề |
| G08 | Chọn handle từ context; thực thi vẫn thiếu key |
| G09 | Giữ chủ đề, đổi wiki sang en |
| G10 | Yêu cầu gửi → clarify yes_no; không chứng minh gửi thật |

## B4. Chat evidence

Ba transcript v4 gốc gồm 7 lượt:

| Transcript | Bằng chứng và giới hạn |
|---|---|
| `v4_openrouter_20261110T112624041160.transcript.json` | Ba lượt now/wiki/hn_search và dữ liệu trả về |
| `v4_openrouter_20261110T112651615121.transcript.json` | Hỏi tên công ty rồi tra OpenAI; lượt hỏi bổ sung có status **answered**, vì model hỏi bằng text và không gọi clarify; không phải waiting_for_user |
| `v4_openrouter_20261110T112704698170.transcript.json` | Hai lần hỏi lại/yes_no; **chưa có draft được duyệt rồi gửi Telegram thật** |

Chat public v6 lưu riêng tại `public_app_smoke.json`: URL, thời điểm +07:00, đường dẫn script phiên public, artifact/hash và từng lượt. Không sửa transcript v4 thành bằng chứng mới.

## B5. Unit tests và bonus

**Bản trước sửa: 104 passed, không phải 101. `test_tools_todo.py`: 27 test, không phải 39.**

Bản hiện tại: **119 passed, 0 failed, 0 skipped**; thêm 15 test hồi quy trong `test_eval_and_delivery.py`: nội dung v4 sai, từ chối kèm lời giải, phản hồi trống, metrics execution, send giả mạo qua agent/chat và console ASCII. Tests offline, HTTP giả; không gửi Telegram thật. Log: `unit_test_results.txt`.

| Hạng mục | Kết luận |
|---|---|
| Ba tool mới | Đủ bắt buộc; chưa đạt bonus “hơn 3” |
| Telegram | **Không nhận bonus gửi thật.** Log chỉ chứng minh hỏi xác nhận; transport test dùng HTTP giả. Runtime/UI tắt gửi. Chưa có xác nhận gắn chính xác draft/người nhận |
| Policy/arXiv | Extension v6 chọn tool/args 10/10, không ghi nhận lỗi tool trong lần chạy này; chưa chứng minh mọi tài liệu/câu trả lời đều đúng |
| UI public | URL được kiểm tra HTTP/WebSocket/chat trên đúng app; tunnel tạm thời, chưa kiểm tra bố cục bằng ảnh |
| Poster | Chưa làm; tùy chọn |
| Small Local Model Challenge | Chưa làm; tùy chọn; không có số liệu bonus |

## B6. Tái lập và giới hạn

Chạy trong `starter_v0/`, với `.venv` đã cài requirements:

```powershell
.venv/Scripts/python.exe -m pytest tests/ -q
.venv/Scripts/python.exe -X utf8 run_eval.py --version v6 --provider openrouter --suite base
.venv/Scripts/python.exe -X utf8 run_eval.py --version v6 --provider openrouter --suite extension --eval-cases data/eval_research_extension.json
.venv/Scripts/python.exe -X utf8 run_eval.py --version v6 --provider openrouter --suite group --eval-cases data/eval_group.json
.venv/Scripts/python.exe -X utf8 scripts/verify_public_app.py https://karl-evans-tower-matrix.trycloudflare.com
```

Prompt quy định hành vi; tools.yaml mô tả routing/args; runtime chặn gửi; evaluator tách routing, text no_tool và lỗi thực thi. Prompt không thay được guard runtime. Bonus Telegram cần duyệt đúng draft/người nhận ở host và receipt gửi thật. Cần cấp key Twitter để kiểm chứng chức năng đó; không bịa key/dữ liệu. V6 là một lần chạy mỗi case, chưa đo độ ổn định qua nhiều lần lặp.
