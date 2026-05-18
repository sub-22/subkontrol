---
description: Morai Merge Protocol — merge parallel worktrees sau khi tất cả waves committed
---

# MERGE PROTOCOL — Post-Parallel Worktree Merge

Được kích hoạt bởi Spawner sau khi `commit_wave()` trả về `all_done: true`.

## Mục tiêu

Sau khi N sub-agents commit N branches riêng biệt, Orchestrator merge tất cả
vào một feature branch duy nhất, sau đó tạo **1 PR** cho toàn bộ ticket.

---

## Merge Strategy

**Chiến lược:** Sequential merge với `--no-ff` (giữ rõ history từng task).

```
Base branch: feat/{ticket_id}   ← tạo từ main trước khi spawn
  ← merge feat/{ticket_id}-task-1  (wave 1)
  ← merge feat/{ticket_id}-task-3  (wave 1)
  ← merge feat/{ticket_id}-task-2  (wave 2)
  ← ...
→ Single PR từ feat/{ticket_id} vào main
```

**Thứ tự merge:** Wave 1 trước, sau đó Wave 2, ... Trong cùng wave → merge theo `priority` trong task JSON (P0 trước).

---

## Quy trình

### Bước 1 — Tạo / checkout feature branch
```
morai-git: get_current_branch()
# Nếu chưa có feature branch:
morai-git: create_branch("feat/{ticket_id}")
```

### Bước 2 — Merge từng worktree branch theo thứ tự

Với mỗi task branch (theo wave order, priority order):
```
git merge feat/{ticket_id}-{task_id} --no-ff -m "merge: {task_id} into {ticket_id}"
```

Nếu merge **thành công** → tiếp tục task tiếp theo.

Nếu merge **conflict** → xem Conflict Resolution bên dưới.

### Bước 3 — Verify sau khi merge

```
morai-git: status()   ← không còn unmerged files
morai-rag: search("changed files structure", namespace)   ← RAG đã index, dùng search thay list
```

Nếu project có test runner:
```
Chạy test suite → nếu fail → STOP, báo Dev trước khi tạo PR
```

### Bước 4 — Tạo PR

```
morai-git: push("feat/{ticket_id}")
morai-git: create_pr(
  title="feat({ticket_id}): {spec_title}",
  body=<điền từ template templates/pr/feature.md>,
  base="main"
)
```

PR body phải include:
- Link spec: `specs/{ticket_id}.md`
- Tasks implemented: list từ wave plan
- Files changed per task
- Test results

### Bước 5 — Update pipeline state + Cleanup

```
morai-pipeline: transition(ticket_id, "DEV_ALL_COMMITTED",
  context={"pr_url": pr_url, "feature_branch": "feat/{ticket_id}"})

morai-pipeline: transition(ticket_id, "REVIEW_RUNNING")
```

> **Cleanup worktrees (sau khi PR merged):** `git worktree remove {path}` cho mỗi worktree.
> Làm sau khi reviewer approve và merge PR — không làm trước đó.

---

## Conflict Resolution

### Automatic conflict (non-overlapping files)
```
Conflict chỉ ở whitespace / imports → auto-resolve nếu có thể
→ Tiếp tục merge
```

### Conflict cần human

```
1. DỪNG merge tại task bị conflict
2. Báo Dev chi tiết:

⚠️ Merge conflict: feat/{ticket_id}-{task_id}
Conflicted files:
  - src/models/user.py (lines 45-67)

Tasks đã merged thành công: TASK-1, TASK-3
Task bị conflict: TASK-2

Anh resolve conflict rồi em tiếp tục?

3. Dev resolve → nói "đã resolve"
4. Orchestrator: git merge --continue
5. Tiếp tục từ bước 2 với task tiếp theo
```

### Conflict không thể resolve

```
1. Abort merge: git merge --abort
2. Transition: block_pipeline(ticket_id, reason="Merge conflict at TASK-X, cần human resolve")
3. Preserve: giữ tất cả worktrees để Dev có thể inspect
4. Báo cáo: danh sách branches cần manual review
```

---

## Parallel Branch Safety Rules

1. **Không xóa worktree** cho đến khi PR được merge vào main
2. **Không rebase** worktree branches sau khi sub-agent đã commit — mất traceability
3. **Mỗi worktree branch là immutable** sau spawn — chỉ được thêm commits, không force push
4. **Worktree naming** phải consistent: `feat/{ticket_id}-{task_id.lower()}`

---

## Diagram tổng thể

```
main
  │
  ├─ feat/PROJ-123          ← feature branch (merge target)
  │      │
  │      ├─ feat/PROJ-123-task-1  ← worktree 1 (Agent A)
  │      ├─ feat/PROJ-123-task-3  ← worktree 2 (Agent B)
  │      └─ feat/PROJ-123-task-2  ← worktree 3 (Agent C, wave 2)
  │
  └─ (sau merge) feat/PROJ-123 → PR → merge vào main
```
