---
description: Morai Onboard — bootstrap knowledge repo từ Confluence + Jira + codebase cho project mới
---

# Morai Onboard

Tổng hợp knowledge cho project: pull docs từ Confluence, tickets từ Jira, index vào RAG.
Dùng khi bắt đầu làm việc với project mới có đầy đủ tooling.

## Input
$ARGUMENTS — tên project (optional, sẽ hỏi nếu không có)

## Quy trình

### Bước 1 — Preflight: chạy /morai:doctor

Chạy `/morai:doctor` với filter `jira confluence` để kiểm tra kết nối trước.

Đọc `DOCTOR_RESULT` trả về:

**Nếu cả jira lẫn confluence đều là `error` (server không khởi động):**
```
Cả morai-jira lẫn morai-confluence đều không hoạt động.
Sếp thử /reload-plugins rồi chạy lại nhé.
```
Dừng.

**Nếu một hoặc cả hai là `shadow` (chưa có credentials):**
Thông báo rõ tool nào chưa configure, sau đó hỏi:
```
morai-jira / morai-confluence chưa có credentials.
Sếp muốn:
1. Tiếp tục — bỏ qua tool chưa configure, dùng cái còn lại
2. Dừng lại — vào Plugin Settings → morai để điền credentials rồi chạy lại
```
Nếu chọn dừng → kết thúc.
Nếu chọn tiếp tục → tự động thêm `--no-jira` hoặc `--no-confluence` tương ứng.

**Nếu tất cả `ok`:** tiếp tục bình thường.

### Bước 2 — Collect thông tin project

Hỏi lần lượt (bỏ qua nếu $ARGUMENTS đã có):

1. **Tên project** (bắt buộc): dùng để tạo `{project-name}-design` repo
2. **Jira project key** (chỉ hỏi nếu jira = ok, ví dụ: PROJ)
3. **Confluence space key** (chỉ hỏi nếu confluence = ok, ví dụ: MYSPACE)
4. **Git org** (optional): để trống nếu không push lên git

### Bước 3 — Tìm onboard.py trong plugin cache

```bash
find ~/.claude/plugins/cache/morai -name "onboard.py" -path "*/scripts/*" 2>/dev/null | head -1
```

Nếu không tìm được → báo lỗi:
```
Không tìm thấy Morai plugin cache. Sếp thử /reload-plugins rồi chạy lại nhé.
```

Xác định plugin root:
```bash
dirname $(dirname <path-onboard.py>)
```

### Bước 4 — Build và chạy lệnh

Build args dựa trên kết quả doctor + thông tin đã collect:
- jira = ok và có key → `--project <key>`, ngược lại → `--no-jira`
- confluence = ok và có space → `--confluence-space <key>`, ngược lại → `--no-confluence`
- Có git org → `--git-org <org>`
- Luôn thêm `--synthesize` để scan codebase sau khi onboard

```bash
uv run --project <plugin-root> python <path-onboard.py> \
  --project-name <tên> \
  [--project <jira-key> | --no-jira] \
  [--confluence-space <space> | --no-confluence] \
  [--git-org <org>] \
  --synthesize
```

### Bước 5 — Báo kết quả

Khi xong:
```
Onboard xong sếp. Knowledge repo đã được tạo tại ./{project-name}-design/
Morai đã index codebase + docs — sẵn sàng làm việc.
```

Nếu lỗi 401 trong quá trình chạy:
```
Authentication lỗi với [Jira/Confluence]. Token có thể đã hết hạn.
Sếp vào Plugin Settings → morai để cập nhật credentials rồi chạy lại nhé.
```
