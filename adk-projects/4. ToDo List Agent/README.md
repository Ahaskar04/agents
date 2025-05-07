# 📦 Artifact System in Google ADK

Artifacts in the Agent Development Kit (ADK) represent **versioned binary or textual data**, allowing agents and tools to **store, retrieve, and persist data** across sessions or users.

---

## 🚀 What Are Artifacts?

Artifacts are binary blobs wrapped as `google.genai.types.Part` objects — typically representing files like `.txt`, `.pdf`, `.png`, or serialized data.

Each artifact:

- Is **named** via a filename (e.g., `to-do.txt`)
- Can be **versioned** (each save creates a new version)
- Is **scoped** to either a session or a user (`user:` prefix)

---

## 🧠 Why Use Artifacts?

Artifacts are ideal for:

- Persisting to-do lists, user-generated files, or results across sessions
- Managing large or binary data (vs. small config in session state)
- Versioning results without overwriting

---

## 🛠 Creating and Saving Artifacts

You can save artifacts using the `save_artifact()` method on a `ToolContext` or `CallbackContext`.

```python
import google.genai.types as types

data_bytes = b"example content"
artifact = types.Part.from_data(data=data_bytes, mime_type="text/plain")
context.save_artifact("filename.txt", artifact)
```

````

Each call saves a **new version**.

---

## 📥 Loading Artifacts

You can retrieve the latest or specific version:

```python
artifact = context.load_artifact("filename.txt")
if artifact:
    content = artifact.inline_data.data.decode("utf-8")
```

---

## 📂 Listing Artifacts

Only in `ToolContext`, you can list all accessible filenames:

```python
tool_context.list_artifacts()
# Returns: ['to-do.txt', 'user:settings.json']
```

---

## 🧭 Namespacing

- `"file.txt"` → tied to session
- `"user:file.txt"` → tied to user (available across all sessions)

---

## 🗃 Artifact Storage Options

ADK provides two implementations:

| Implementation            | Storage              | Use Case                   |
| ------------------------- | -------------------- | -------------------------- |
| `InMemoryArtifactService` | RAM                  | Testing, demos (ephemeral) |
| `GcsArtifactService`      | Google Cloud Storage | Production (persistent)    |

---

## 🧩 Example Use Case: To-Do List Tool

```python
def add_task(tool_context, task: str):
    old = ""
    try:
        artifact = tool_context.load_artifact("to-do.txt")
        if artifact:
            old = artifact.inline_data.data.decode("utf-8")
    except: pass

    updated = old + task + "\n"
    part = types.Part.from_data(data=updated.encode("utf-8"), mime_type="text/plain")
    tool_context.save_artifact("to-do.txt", part)
```

---

## ⚠️ Best Practices

- Always specify a correct `mime_type`
- Use `"user:"` prefix for persistent user-specific files
- Handle missing artifacts gracefully (check for `None`)
- Avoid massive binary blobs unless necessary

---

## 🧼 Cleanup

Artifacts are **immutable** and accumulate versions. For GCS:

- Use [GCS lifecycle policies](https://cloud.google.com/storage/docs/lifecycle) or
- Write an admin tool using `artifact_service.delete_artifact()`

---

## ✅ Summary

Google ADK's Artifact system makes it easy to manage named, versioned, and persistent data, especially for workflows involving file-like outputs, user history, or assistant memory.

```

```
````
