# Backlog — {project_name}

Nguồn ticket local cho project không dùng Jira. Path: `.morai/tasks/backlog.md`
(per-project, gitignored). Parsed bởi `agents/task_fetcher.md` (LOCAL mode) và `/morai:routine`.

Format mỗi task — `record_task()` cũng ghi đúng format này:

## SK-101 · [High] Tiêu đề task ngắn gọn
- status: todo
- created: 2026-06-10
- ac: acceptance criteria — 1-2 dòng, đủ để biết "xong" nghĩa là gì

## SK-102 · [Medium] Task thứ hai
- status: doing
- created: 2026-06-10
- ac: ...

<!--
Quy ước:
- status: todo | doing | done — task done giữ nguyên trong file (history), fetcher bỏ qua
- priority: [High] | [Medium] | [Low]
- ticket id tự đặt theo project (SK-x, TASK-x...) — không cần Jira
-->
