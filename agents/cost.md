---
description: Morai Cost Management — model routing, token budget, context compression
---

# COST — Token Budget & Model Routing

Morai tự chọn model phù hợp với từng task để tối ưu cost/quality.
Default budget: **200,000 tokens per pipeline** (configurable qua `MORAI_BUDGET_TOKENS`).

---

## Model Routing Table

| Task size / Type | Model | Lý do |
|-----------------|-------|-------|
| XS — typo, config, 1-line | `haiku` | Fast + cheap, không cần reasoning sâu |
| S — simple bug, update config | `haiku` | Đủ dùng cho changes nhỏ |
| M — feature module, refactor | `sonnet` | Balanced: quality + cost |
| L — complex feature, multi-service | `sonnet` | Reasoning tốt, still cost-effective |
| XL — architecture change, migration | `opus` | Cần deep reasoning |
| `/morai:sparring` (bất kỳ size) | `opus` | Strategic thinking, cần breadth |
| `/morai:security` | `sonnet` | Pattern recognition đủ |
| Sub-agents (parallel, wave) | `haiku` | Volume execution, cost efficiency |
| `/morai:architect` (design phase) | `sonnet` | Technical analysis |
| `/morai:ba` (spec writing) | `haiku` | Structured writing task |
| `/morai:reviewer` | `sonnet` | Nuanced code review |

**Khi nào dùng Opus:**
- Task yêu cầu multi-step reasoning với nhiều trade-offs
- Decision có tác động lớn đến architecture
- User explicit: "dùng model tốt nhất"

**Khi nào giữ Sonnet (không downgrade Haiku):**
- Security review — false negative cost cao hơn token cost
- Dev guided GATE 1 — approach quality quan trọng
- Incident triage — cần reason đúng severity

---

## Budget Lifecycle

```
Pipeline created: budget = 200,000 tokens
    │
    ├─ Mỗi skill call: morai-pipeline: record_token_usage(...)
    │
    ├─ 80% used (160k tokens):
    │    → alert: "WARNING: Budget 80% used"
    │    → Action: compress context (archive old messages, summarize)
    │
    ├─ 95% used (190k tokens):
    │    → alert: "CRITICAL: Budget 95% used"
    │    → Action: pause pipeline, checkpoint, start fresh context for next step
    │    → Publish: internal.budget_critical_95
    │
    └─ Pipeline complete → log final cost via get_pipeline_cost()
```

---

## Context Compression (khi 80%+)

Khi budget warning:

```
1. Archive old context:
   - Messages từ skills đã complete → không cần giữ detail
   - Chỉ giữ: final output của mỗi step (spec.md path, design path, PR URL)

2. Summarize active context:
   "Pipeline PROJ-123: BA done (specs/PROJ-123.md), PM done (5 tasks, Wave plan: 2 waves),
    Currently: DEV Wave 1 — TASK-1 approach approved, implementing chunk 2/3"

3. Reset context window:
   → Đọc lại chỉ những gì cần cho bước tiếp theo
   → Không đọc lại toàn bộ conversation history
```

---

## Token Tracking — Khi nào gọi

Gọi `morai-pipeline: record_token_usage()` sau các LLM calls sau:

| Call | Input estimate | Output estimate |
|------|---------------|----------------|
| BA spec generation | 8,000 | 3,000 |
| PM task breakdown | 5,000 | 2,000 |
| Dev approach (GATE 1) | 10,000 | 2,000 |
| Dev implement chunk | 15,000 | 5,000 |
| Reviewer review | 12,000 | 3,000 |
| Security audit | 10,000 | 2,000 |
| QA test plan | 8,000 | 2,500 |

*Đây là estimates — dùng actual numbers từ API response khi có.*

---

## Cost Visibility

```
morai-pipeline: get_pipeline_cost("PROJ-123")
→ {
    total_tokens: 45,000,
    budget_used_pct: 22.5,
    estimated_usd: 0.48,
    by_skill: {
      "ba": {input: 8000, output: 3000, model: "haiku"},
      "pm": {input: 5000, output: 2000, model: "haiku"},
      "dev": {input: 15000, output: 5000, model: "sonnet"}
    }
  }

morai-pipeline: get_cost_summary_all()
→ All pipelines sorted by token usage — identify expensive skills
```

---

## Optimize Cost Tips

1. **BA và PM luôn dùng Haiku** — structured output, không cần Sonnet/Opus
2. **Sub-agents (parallel) dùng Haiku** — nhiều agents × cost = exponential nếu Sonnet
3. **RAG search trước khi gọi LLM** — context tốt hơn = output ngắn hơn = ít tokens hơn
4. **Chunk nhỏ trong dev** — 1 function/time tốt hơn cả module → dễ review, ít re-generate
5. **Skip Slack trong dev env** — không tốn tokens viết Slack messages khi testing
