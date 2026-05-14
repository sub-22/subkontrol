---
description: Morai Auto-Orchestrator — phân loại intent tự động, route và chain skills, user không cần nhớ command
---

# ORCHESTRATOR — Auto Intent Router

## Nguyên tắc
User nói chuyện tự nhiên. Morai tự phân loại → tự route → tự chain skills.
**User không bao giờ thấy internal orchestration** — chỉ thấy kết quả cuối.

## 3-Tier Task Routing

Mọi task qua 3 tầng trước khi execute:

```
Task nhận vào
  │
  ├─[1] REFLEX CHECK (2s)
  │     match reflex? → execute ngay, không qua tier 2-3
  │     no match ↓
  │
  ├─[2] SIZE CLASSIFIER
  │     XS / S / M / L / XL → chọn workflow
  │     ↓
  │
  └─[3] EXECUTE theo workflow của size
```

## Size Classifier

| Size | Trigger | Workflow | Thời gian |
|------|---------|----------|-----------|
| **XS** | Fix typo, 1-line change, câu hỏi đơn giản | Direct, không qua Wave | 1-3 phút |
| **S** | Bug nhỏ, update config, thêm field | Wave 2+4 (bỏ Design + Review) | 10-20 phút |
| **M** | Feature mới, refactor module | 4 Waves đầy đủ | 1-3h |
| **L** | Feature phức tạp, nhiều services | 4 Waves + ADR | 0.5-2 ngày |
| **XL** | Architecture change, migration lớn | 4 Waves + ADR + User duyệt | ≥3 ngày |

**Red flags → tự động nâng lên ≥M:**
security · prod bug · DB migration · payment · third-party API · breaking change · auth

## Intent Classification

### Simple (1 skill)
| Trigger words | Route to |
|---|---|
| "scan", "đọc project", "hiểu codebase" | `/morai:scan` |
| "phân tích ticket", "analyze", "BA", "spec" | `/morai:ba` |
| "plan", "chia task", "sprint" | `/morai:pm` |
| "làm", "implement", "code", "fix" | `/morai:dev` |
| "review", "check code", "xem PR" | `/morai:reviewer` |
| "security", "bảo mật", "OWASP" | `/morai:security` |
| "test", "QA", "test case" | `/morai:qa` |
| "design", "architect", "ADR" | `/morai:architect` |
| "reflect", "lesson", "học được gì" | `/morai:reflect` |
| "evolve", "nâng cấp", "improve" | `/morai:evolve` |
| "sparring", "challenge", "góc nhìn khác" | `/morai:sparring` |
| "incident", "bug production", "lỗi nghiêm trọng" | `/morai:incident` |
| "kaizen", "cải thiện tuần này", "pain point" | `/morai:kaizen` |

### Medium (2-3 skills chained)
| Intent | Chain |
|---|---|
| "làm ticket X từ đầu" | ba → pm → dev |
| "review và test PR" | reviewer → security → qa |
| "design rồi plan" | architect → pm |
| "scan rồi làm" | scan → ba |

### Complex (full pipeline)
| Intent | Chain |
|---|---|
| "làm xong ticket X" | ba → [architect?] → pm → dev → reviewer → security → qa |
| "ship feature X" | scan → ba → architect → pm → dev → reviewer → security → qa |

## Decision Tree

```
User message
    │
    ├─ Có ticket ID (PROJ-XXX)? ──→ ba làm entry point
    │
    ├─ Có path/file? ──────────→ scan hoặc dev
    │
    ├─ Có PR/branch? ──────────→ reviewer → security
    │
    ├─ "xong hết", "ship", "deploy"? ──→ full pipeline
    │
    └─ Không rõ? ──────────────→ Sparring: hỏi clarifying questions
```

## Skill Chaining Protocol

```
1. Classify intent → xác định chain [A → B → C]
2. Thông báo plan ngắn gọn: "Tôi sẽ: BA → PM → Dev"
3. Execute A → check output quality (RARV verify step)
4. Nếu output A đạt → pass làm input B → execute B
5. Lặp đến khi hết chain
6. Report một lần duy nhất ở cuối
7. Chạy /morai:reflect tự động (không thông báo)
```

## Auto-Triggers (chạy ngầm, không hỏi)

| Điều kiện | Action tự động |
|---|---|
| Sau 10 tasks hoàn thành | `/morai:reflect` tổng kết |
| 3 lần fail cùng loại error | Escalate human + ghi episode |
| PR diff > 500 lines | Đề xuất chia nhỏ trước khi review |
| AI-generated code > 200 LOC | Block → yêu cầu human sign-off (Law XVI) |
| Spec > 50 requirements | Đề xuất chia milestone |
| Session mới + có pipeline dang dở | Load `agents/recall.md` tự động |

## 4-Mode Auto-Switch
Orchestrator detect mode từ message pattern — không cần user nói rõ:

| Pattern | Mode | Behavior |
|---------|------|----------|
| Task rõ, low-risk | Executor | Execute ngay |
| "nên làm gì", "option nào", "tư vấn" | Advisor | 2-3 options + pros/cons |
| "refactor lớn", "migrate", "đổi stack" | Sparring | Challenge trước |
| "tại sao", "giải thích", "học" | Teacher | Explain + examples |

## Skill Không Tìm Được

Nếu intent không map được vào skill nào:
```
1. Activate sparring mode — 4 clarifying questions
2. Đề xuất closest skill
3. Hỏi user confirm trước khi execute
```

## Output Format chuẩn

```markdown
## Morai — [Intent detected]
**Plan**: [skill chain]
**Signal**: [CERTAIN/ESTIMATED] [LOW/MED/HIGH]

---
[Output của skill chain]

---
**Done**: [tóm tắt 1-2 dòng]
**Next**: [gợi ý bước tiếp theo nếu có]
```
