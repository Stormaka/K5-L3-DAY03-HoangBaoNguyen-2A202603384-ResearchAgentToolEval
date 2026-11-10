---
name: now
track: bonus
kind: control
requires_env: []
inputs: [tz]
outputs: [iso, date, time, weekday_vi]
side_effect: false
---
# now

Trả về ngày giờ hiện tại (local hoặc utc) + thứ bằng tiếng Việt.
Giúp agent neo các từ thời gian tương đối ("hôm nay", "tuần này") trước khi tra tin.
Hoàn toàn local, không gọi mạng.
