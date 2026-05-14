---
description: Morai Context Gateway — digital twin của hệ thống đang vận hành, active missions, current state
---

# CONTEXT GATEWAY — Active System State

## Mục đích
Lưu trạng thái **đang diễn ra** — không phải lịch sử, không phải reference.
Agents đọc file này để biết hệ thống đang ở đâu RIGHT NOW.

```
Context Gateway = "Morai đang làm gì? Hệ thống đang ra sao?"
Knowledge Gateway = "Morai đã học gì? Biết gì về domain?"
docs/ = "Reference cho humans đọc"
```

## Active Pipelines
<!-- Cập nhật tự động bởi morai-memory: save_pipeline_state() -->
```
Đang chạy: [none]
Blocked: [none]
Completed hôm nay: [none]
```

## System Digital Twin
<!-- Cập nhật khi /morai:scan được chạy -->
```
Last scanned: [chưa có]
Active projects: [none]
RAG namespaces: []
```

## Active Missions
<!-- User-defined goals đang theo đuổi -->
```
Sprint hiện tại: [chưa set]
Priority tickets: []
Blockers: []
```

## Environment Status
```
morai-rag:        [not checked]
morai-jira:       [stub — chưa implement]
morai-confluence: [stub — chưa implement]
morai-slack:      [stub — chưa implement]
morai-file:       [working]
morai-git:        [working]
morai-memory:     [working]
```

## Cách update Context Gateway
Agents tự update sau mỗi action quan trọng:
```
morai-file: write_file("agents/context_gateway.md", updated_content)
```

Hoặc user chạy `/morai:scan` → tự refresh System Digital Twin.
