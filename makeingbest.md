Phase 1 (1-2 tuần): FSM pipeline + Permission model                                                 
    → Foundation. Không có FSM thì parallelism sẽ corrupt state.                                      
                                                                                                      
  Phase 2 (2-4 tuần): Multi-agent parallelism                                                         
    → Biggest impact. Dev tasks chạy song song = 3x faster.                                           
                                                                                                      
  Phase 3 (1 tuần): HITL gates standardized                                                           
    → Prerequisite cho production use.                                                                
                                                                                                      
  Phase 4 (ongoing): Event triggers + Cost management                                                 
    → Autonomy thực sự. giải thích lại các phase                                                      

● Giải thích chi tiết 4 Phases — Morai → Agents OS

  ---
  Phase 1 — FSM Pipeline + Permission Model (1-2 tuần)

  Tại sao làm trước?

  Morai hiện lưu pipeline state bằng JSON file + skill tự gọi save_pipeline_state() thủ công. Không có
   gì ngăn một skill nhảy từ ba thẳng sang qa bỏ qua pm và dev. Không có rollback. Không có
  pre-condition validation.

  Khi Phase 2 (parallelism) chạy nhiều agents cùng lúc, nếu state không có FSM, hai agents có thể ghi
  đè state của nhau → corrupt pipeline, mất track.

  FSM Pipeline — Cụ thể là gì

  Định nghĩa tất cả states hợp lệ và transitions có điều kiện:

  IDLE
    → BA_RUNNING      (pre: ticket_id tồn tại)
    → BA_DONE         (pre: specs/<id>.md exists)
    → ARCHITECT_RUNNING (pre: feature phức tạp theo R-010)
    → ARCHITECT_DONE  (pre: designs/<id>-detail.md exists)
    → PM_RUNNING      (pre: BA_DONE hoặc ARCHITECT_DONE)
    → PM_DONE         (pre: tasks/<id>/index.json exists)
    → DEV_RUNNING     (pre: PM_DONE, task tồn tại)
    → DEV_REVIEWING   (pre: code written, waiting for Dev — guided mode)
    → DEV_COMMITTED   (pre: Dev approved, commit exists)
    → REVIEW_RUNNING  (pre: DEV_COMMITTED, PR exists)
    → REVIEW_DONE     (pre: review file written, verdict != REQUEST_CHANGES)
    → SECURITY_RUNNING
    → SECURITY_DONE   (pre: verdict = PASS hoặc WARN)
    → QA_RUNNING
    → COMPLETE        (pre: all DoD items done)
    → BLOCKED         (any step, với block_reason)
    → FAILED          (L1/L2 incident)

  Invalid transition → Judge block + log. Không cần skills tự enforce, FSM enforce tập trung.

  Implement bằng cách extend morai-memory server: thêm transition_pipeline(ticket_id, new_state) với
  validation built-in.

  Permission Model — Cụ thể là gì

  Hiện tại BA skill có thể gọi git commit. QA skill có thể xóa source files. Không có gì ngăn cả.

  Định nghĩa một permissions.yaml:

  skills:
    ba:
      read:  [morai-jira.*, morai-confluence.*, morai-rag.*]
      write: [morai-file.write_file, morai-memory.*]
      deny:  [morai-git.commit, morai-git.push, morai-file.delete_file]

    dev-guided:
      read:  [morai-file.*, morai-rag.*, morai-git.status, morai-git.diff]
      write: [morai-file.write_file, morai-git.commit, morai-git.push]
      deny:  [morai-git.create_pr]  # PR chỉ khi Dev nói

    dev-auto:
      read:  [morai-file.*, morai-rag.*, morai-git.*]
      write: [morai-file.*, morai-git.*]
      deny:  []

    reviewer:
      read:  [morai-git.*, morai-file.read_file, morai-rag.*]
      write: [morai-file.write_file, morai-git.add_pr_comment]
      deny:  [morai-git.commit, morai-git.push, morai-file.delete_file]

  morai-file và morai-git servers check caller identity trước khi execute. Nếu skill không có
  permission → return error thay vì execute.

  Done khi nào?

  - Transition invalid bị block với message rõ ràng
  - Skill gọi tool ngoài permission → error, không execute
  - Pipeline có thể rollback về state trước nếu step fail
  - Judge đọc FSM state thay vì đọc JSON tự do

  ---
  Phase 2 — Multi-agent Parallelism (2-4 tuần)

  Tại sao đây là biggest impact?

  Ticket có 5 tasks → hiện tại: TASK-1 done → TASK-2 done → ... = sequential, tổng thời gian là sum.

  Với parallelism: TASK-1 || TASK-2 || TASK-3 chạy đồng thời trong isolated worktrees → thời gian =
  max(tasks), không phải sum.

  3-5 tasks độc lập có thể giảm thời gian 60-70%.

  Cụ thể là gì

  Claude Code đã có sẵn hai primitives cần thiết: Agent tool (spawn sub-agent) và EnterWorktree
  (isolated git branch). Morai chỉ cần orchestration layer bên trên.

  Spawner protocol (agents/spawner.md) sẽ định nghĩa:

  Orchestrator nhận N tasks có thể parallelize (không có dependency lẫn nhau)
      │
      ├─ Với mỗi task: EnterWorktree(branch=feat/<ticket>-<task>)
      ├─ Spawn Agent(prompt=dev_guided_instructions, task=TASK-N, worktree=...)
      ├─ Tất cả agents chạy song song
      │
      ├─ Mỗi agent: implement → GATE 1 (approach) → Dev review → commit
      │
      └─ Khi tất cả COMMITTED:
           Orchestrator merge worktrees → resolve conflicts nếu có
           → reviewer chạy trên merged branch

  Dependency graph — không phải task nào cũng parallel được:

  TASK-1 (DB schema)
  TASK-2 (API endpoint) — depends_on: TASK-1
  TASK-3 (Frontend form) — độc lập
  TASK-4 (Unit tests) — depends_on: TASK-2

  Graph:
    TASK-1 → TASK-2 → TASK-4
    TASK-3 (independent)

  Parallel groups:
    Wave 1: TASK-1 || TASK-3
    Wave 2: TASK-2 (sau TASK-1 done)
    Wave 3: TASK-4 (sau TASK-2 done)

  PM skill sẽ phân tích depends_on trong task JSON để sinh ra parallel waves.

  Thách thức chính

  Merge conflicts: Hai agents sửa cùng file → conflict. Cần merge protocol:
  - Agents write vào namespaced paths khi có thể
  - Conflict → escalate Orchestrator → human resolve

  Context isolation: Mỗi sub-agent có context window riêng, không share với Orchestrator. Sub-agent
  cần receive đủ context (spec, conventions, relevant code) trong prompt ban đầu — không thể hỏi
  Orchestrator mid-task.

  Gate coordination: Khi 3 agents cùng chờ Dev review (GATE 1), Dev cần review 3 approaches cùng lúc —
   UX phức tạp. Giải pháp: queue gate requests, Dev review lần lượt.

  Done khi nào?

  - PM skill sinh parallel wave plan từ dependency graph
  - Orchestrator spawn N sub-agents vào N worktrees
  - Agents hoàn thành độc lập, merge về main branch
  - Reviewer chạy trên merged result

  ---
  Phase 3 — HITL Gates Standardized (1 tuần)

  Tại sao là prerequisite cho production?

  Hiện tại gates là text không enforce: "DỪNG — Chờ Dev phản hồi" là instruction cho LLM, không phải
  mechanism. Nếu LLM "quên" dừng → auto-proceed.

  Với parallelism (Phase 2), có thể có 5 gates pending cùng lúc mà không biết cái nào cần unblock
  trước.

  Cụ thể là gì

  Gate types cần support:

  ┌─────────┬──────────────────────────────────────┬─────────────────────────────────────┐
  │  Type   │               Use case               │           Response format           │
  ├─────────┼──────────────────────────────────────┼─────────────────────────────────────┤
  │ APPROVE │ "Approach này ok không?"             │ yes / no / change                   │
  ├─────────┼──────────────────────────────────────┼─────────────────────────────────────┤
  │ REVIEW  │ "Code chunk này anh xem thử"         │ approve / request_changes + comment │
  ├─────────┼──────────────────────────────────────┼─────────────────────────────────────┤
  │ CHOICE  │ "Option A hay B?"                    │ A / B / C                           │
  ├─────────┼──────────────────────────────────────┼─────────────────────────────────────┤
  │ CONFIRM │ "Commit bây giờ không?"              │ commit / abort                      │
  ├─────────┼──────────────────────────────────────┼─────────────────────────────────────┤
  │ UNBLOCK │ Pipeline stuck, cần human quyết định │ action string                       │
  └─────────┴──────────────────────────────────────┴─────────────────────────────────────┘

  morai-memory extension — thêm gate tracking:

  create_gate(ticket_id, gate_type, question, context, timeout_minutes=30)
  # Returns: gate_id

  resolve_gate(gate_id, response, resolved_by="user")
  # Unblocks pipeline, triggers resume

  get_pending_gates()
  # Returns all gates waiting for human input, sorted by urgency

  Pipeline integration: Khi skill cần human input, thay vì chỉ in text:
  1. Gọi create_gate() → pipeline state → WAITING_FOR_HUMAN
  2. Hiển thị câu hỏi rõ ràng cho user
  3. Khi user respond → resolve_gate() → FSM transition tiếp tục
  
  Timeout handling:
  Gate created → wait N minutes
      ├─ User responds → resolve → continue
      └─ Timeout → escalate (notify, mark BLOCKED, không auto-proceed)

  Session recovery integration: recall.md đọc get_pending_gates() khi start → báo Dev ngay: "Có 2
  gates đang chờ review từ hôm qua."

  Done khi nào?

  - Tất cả gates trong dev/reviewer/security/qa dùng create_gate() thay vì text instruction
  - get_pending_gates() hiển thị queue rõ ràng khi session mới
  - Pipeline không thể tự proceed qua gate — FSM block

  ---
  Phase 4 — Event Triggers + Cost Management (Ongoing)
  
  Event Triggers — Autonomy thực sự

  Hiện tại mọi thứ cần user gõ lệnh. Phase 4 biến Morai thành daemon — tự phản ứng với events mà không
   cần trigger thủ công.

  Event types:

  External events (qua webhook):
    github.pr_opened       → trigger reviewer
    github.pr_merged       → trigger reflect
    github.test_failed     → trigger incident (L3)
    jira.ticket_moved      → trigger ba → pm

  Scheduled events (CronCreate):
    daily   8:00           → check blocked pipelines, report
    weekly  Monday 9:00    → trigger kaizen
    sprint  end_of_sprint  → trigger evolve

  Internal events (Morai-generated):
    tasks_completed >= 10  → trigger reflect
    same_error x3          → escalate + record episode
    pipeline_idle > 2days  → ping Dev

  Event registry (servers/events/server.py):

  subscribe(event_type, handler_skill, filter_conditions)
  publish(event_type, payload)
  get_subscriptions()

  Kết hợp với CronCreate của Claude Code cho scheduled events, và webhook endpoint cho external
  events.

  Cost Management — Kiểm soát ngân sách token

  Không có cost tracking thì không biết pipeline nào đắt, model nào cần, khi nào nên compress.

  Model routing strategy:

  Task size → Model selection:
    XS (typo, config)         → Haiku   (fast + cheap)
    S  (simple bug, 1 file)   → Haiku
    M  (feature module)       → Sonnet  (balanced)
    L  (complex feature)      → Sonnet
    XL (architecture, ADR)    → Opus    (deep reasoning)

  Special cases:
    /morai:sparring            → Opus    (strategic thinking)
    /morai:security            → Sonnet  (pattern recognition)
    Sub-agents in parallel     → Haiku   (volume, cost efficiency)

  Context budget:

  Per-pipeline budget: configurable (default 200k tokens)
  At 80% usage → checkpoint: compress context, archive old steps
  At 95% usage → pause, summarize, start fresh context for next step

  Cost tracker (extend morai-memory):

  record_token_usage(pipeline_id, step, model, input_tokens, output_tokens)
  get_pipeline_cost(pipeline_id)     # Total cost estimate
  get_cost_breakdown_by_skill()      # Which skills are most expensive
  suggest_model_downgrade(task_size) # "This task can use Haiku instead"

  Done khi nào?

  Phase 4 không có "done" — nó là ongoing optimization loop:
  - Tuần 1: Event registry + 3-4 external webhooks hoạt động
  - Tuần 2: Cost tracking + model router basic
  - Ongoing: Thêm event subscriptions, tinh chỉnh model routing theo data thực tế

  ---
  Dependency graph giữa các phases

  Phase 1 (FSM + Permissions)
      ↓ required by
  Phase 2 (Parallelism)  ←── Phase 3 (HITL) — cần gate coordination cho parallel agents
      ↓ enables
  Phase 4 (Events)       ←── Phase 3 (HITL) — event triggers cần gate protocol

  Phase 3 thực ra nên làm song song với Phase 2, không phải sau. Parallel agents mà không có
  standardized gates sẽ flood Dev với review requests không có structure.

  Thực tế nên là:
  Tuần 1-2:  Phase 1 (FSM core + permissions schema)
  Tuần 2-3:  Phase 3 (HITL gates — implement song song khi FSM xong)
  Tuần 3-6:  Phase 2 (Parallelism — cần cả FSM lẫn HITL trước)
  Ongoing:   Phase 4 (Events + Cost)


┌─────────────────┬──────┬──────┬──────┬───────┬───────┬──────────┬──────────────┬──────────┐
  │                 │ Sour │ spec │ plan │ desig │ revie │ tests/*. │              │          │ 
  │      Skill      │ ce   │  s/  │  s/  │  ns/  │  ws/  │    md    │   .morai/    │ git ops  │ 
  │                 │ code │      │      │       │       │          │              │          │ 
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤
  │ scan            │ read │ —    │ —    │ —     │ —     │ —        │ write(knowle │ read     │ 
  │                 │      │      │      │       │       │          │ dge/)        │          │ 
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤
  │ ba              │ —    │ writ │ —    │ —     │ —     │ —        │ read         │ —        │ 
  │                 │      │ e    │      │       │       │          │              │          │
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤ 
  │ architect       │ read │ read │ —    │ write │ —     │ —        │ read         │ read     │ 
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤
  │ pm              │ —    │ read │ writ │ read  │ —     │ —        │ read         │ read     │ 
  │                 │      │      │ e    │       │       │          │              │          │
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤ 
  │ dev             │ WRIT │ read │ read │ read  │ —     │ —        │ read         │ full     │
  │                 │ E    │      │      │       │       │          │              │          │
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤ 
  │ reviewer        │ read │ read │ —    │ read  │ write │ —        │ read         │ read+com │
  │                 │      │      │      │       │       │          │              │ ment     │
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤ 
  │ security        │ read │ read │ —    │ read  │ write │ —        │ read         │ read+com │
  │                 │      │      │      │       │       │          │              │ ment     │
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤  
  │                 │      │      │      │       │       │ write(re │              │          │
  │ qa              │ read │ read │ —    │ —     │ —     │ port     │ read         │ read     │
  │                 │      │      │      │       │       │ only)    │              │          │  
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤
  │ incident        │ read │ —    │ —    │ —     │ —     │ —        │ write        │ read     │
  ├─────────────────┼──────┼──────┼──────┼───────┼───────┼──────────┼──────────────┼──────────┤
  │ reflect/evolve/ │ —    │ —    │ —    │ —     │ —     │ —        │ write        │ read     │
  │ kaizen          │      │      │      │       │       │          │              │          │
  └─────────────────┴──────┴──────┴──────┴───────┴───────┴──────────┴──────────────┴──────────┘
