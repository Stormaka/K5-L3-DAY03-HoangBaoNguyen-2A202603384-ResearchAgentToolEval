---
name: wiki
track: bonus
kind: live_api
requires_env: []
inputs: [topic, lang]
outputs: [title, description, summary, url, source]
provider: Wikipedia REST API
side_effect: false
---
# wiki

Tra cứu bài tóm tắt Wikipedia về một khái niệm / người / tổ chức cụ thể.
`lang` chọn ngôn ngữ wiki (`vi` mặc định, `en` khi chủ đề kỹ thuật).
Trả về 404-friendly `not_found` (không raise) để agent đổi từ khóa hoặc lang thay vì chết cứng.
Không cần API key.
