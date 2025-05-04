# Google ADK – Session, State, and Memory: Key Functions Reference

---

## 🧍 SESSION FUNCTIONS (from `SessionService`)

These manage the lifecycle and retrieval of sessions:

### 🔧 Creating / Getting / Deleting

| Function                                                  | Description                                |
| --------------------------------------------------------- | ------------------------------------------ |
| `create_session(app_name, user_id, session_id, state={})` | Starts a new session                       |
| `get_session(app_name, user_id, session_id)`              | Retrieves a session (with history + state) |
| `delete_session(app_name, user_id, session_id)`           | Deletes a session from storage             |
| `list_sessions(app_name, user_id)`                        | Lists all session IDs for that user/app    |

### 📚 Updating with new events

| Function                                       | Description                                                                              |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `append_event(session: Session, event: Event)` | Adds a new Event (user msg, agent reply, tool call) to the session and updates the state |

---

## 🗃️ STATE FUNCTIONS (within Session object or via Event)

Session state is a **dict** (`session.state`), but you should **NOT update it directly**. Use these methods instead:

### ✅ Safe, Recommended Ways

| Method                                               | Use                                                   |
| ---------------------------------------------------- | ----------------------------------------------------- |
| `output_key` (in `LlmAgent`)                         | Saves agent reply directly to a specific key in state |
| `EventActions(state_delta={...})` → `append_event()` | Appends an Event and updates state in one go          |
| `ToolContext.state[...] = ...` (in tools)            | Sets state from inside a tool (tracked + persisted)   |

### ⚠️ Discouraged (but technically possible)

| Method                         | Risk                                              |
| ------------------------------ | ------------------------------------------------- |
| `session.state["key"] = value` | Won’t persist across DB/VertexAI; not thread-safe |

---

## 🧠 MEMORY FUNCTIONS (from `MemoryService`)

### 📝 Adding to Memory

| Function                                  | Description                                                                        |
| ----------------------------------------- | ---------------------------------------------------------------------------------- |
| `add_session_to_memory(session: Session)` | Ingests a session’s content (events, state) into memory (long-term knowledge base) |

### 🔍 Searching Memory

| Function                                       | Description                                                                 |
| ---------------------------------------------- | --------------------------------------------------------------------------- |
| `search_memory(app_name, user_id, query: str)` | Searches memory for relevant past sessions (returns `SearchMemoryResponse`) |

---

## BONUS: Built-In Tool – `load_memory`

This tool wraps `search_memory()` for LLMs to use. When included in `tools=[...]`, the LLM can call:

```python
load_memory(query="what is my name?")
```

And behind the scenes:

- It calls `memory_service.search_memory(...)`
- The results go back to the agent for use in final response

---

## Summary Table

| Function                        | Used By    | Purpose                             |
| ------------------------------- | ---------- | ----------------------------------- |
| `create_session`                | App/Runner | Start a session                     |
| `get_session`                   | App/Runner | Resume context                      |
| `append_event`                  | Runner     | Add a message/tool/agent reply      |
| `state_delta` in `EventActions` | Agent/tool | Modify state safely                 |
| `ToolContext.state[...]`        | Tools      | Persisted state updates             |
| `add_session_to_memory`         | App        | Save session into searchable memory |
| `search_memory`                 | Tool       | Retrieve knowledge                  |
| `load_memory`                   | Agent tool | Wrapper for `search_memory()`       |