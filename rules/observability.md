# Observability Rules

## Dual-Logged Format
Logs phải readable bởi cả human VÀ AI/regex:

```python
# Format chuẩn
logger.info("[AUTH] user_id=%s action=login status=success duration_ms=%d", uid, ms)

# Hoặc JSON structured
{"scope": "AUTH", "user_id": "123", "action": "login", "status": "success", "duration_ms": 45}
```

Không dùng:
```python
logger.info("User logged in")  # ✗ không searchable, không structured
```

## Correlation ID — Bắt buộc cho Async
Mọi request/job/pipeline phải có `correlation_id` hoặc `trace_id`:
```
Request in → generate X-Correlation-ID
Propagate qua tất cả services/jobs/logs
Dùng để trace full flow khi debug
```

## Evidence-Based Debugging
Khi debug, không đoán — follow evidence:
```
Step 1: Observe — logs, metrics, error messages thực tế
Step 2: Hypothesize — 1-2 hypothesis có evidence support
Step 3: Verify — test hypothesis với minimal change
Step 4: Fix — chỉ fix confirmed root cause
```

Confidence score cho mỗi hypothesis: 1-10.
Không fix cho đến khi có ≥7/10 confidence.

## Morai Pipeline Observability
Mọi pipeline step ghi vào `context_gateway.md`:
```
[timestamp] BA: PROJ-123 — started
[timestamp] BA: PROJ-123 — completed, output: specs/PROJ-123.md
[timestamp] PM: PROJ-123 — started
```

`morai-memory: save_pipeline_state()` sau mỗi step — không bỏ qua.
