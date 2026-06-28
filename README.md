# Aprende+

A local, offline-first English tutor powered by LLMs. Runs entirely on your machine — no internet required, no data leaves your computer.

Aprende+ is designed for kids aged 9–12 at an A1–A2 English level. It uses GGUF quantized models via `llama-cpp-python` to deliver grammar explanations, vocabulary practice, short stories, and conversational exercises through a clean chat interface.

---

## Features

* **100% offline** — once downloaded, everything runs locally. No API keys, no cloud, no tracking.
* **Streaming responses** — tokens appear in real time as the model generates them.
* **Persistent chat history** — conversations are saved in SQLite and restored when you come back.
* **Multiple sessions** — start new chats, switch between them, delete old ones.
* **Topic shortcuts** — one-click prompts for colors, animals, numbers, and short stories.
* **Custom username** — editable profile name, stored in your browser.
* **PDF & OCR support** via `pdfjs-dist` and `tesseract.js` on the frontend.
* **Portable build** — packaged as a single `.exe` with PyInstaller. No Python installation needed.

---

## Stack

| Layer        | Technology                 |
| ------------ | -------------------------- |
| Backend      | Python 3, FastAPI, uvicorn |
| LLM runtime  | llama-cpp-python           |
| Storage      | SQLite                     |
| Frontend     | Svelte 5, Vite             |
| Styling      | Tailwind CSS, Lucide icons |
| Distribution | PyInstaller                |

---

## Recommended model

Download the model and place it inside a `model/` folder in the app directory. The app looks for `model/*.gguf` at startup.

| Model                                                                                                                                                            | File size | Real RAM usage |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------: | -------------: |
| [microsoft_Phi-4-mini-instruct-Q6_K.gguf](https://huggingface.co/bartowski/microsoft_Phi-4-mini-instruct-GGUF/blob/main/microsoft_Phi-4-mini-instruct-Q6_K.gguf) |   3.16 GB |        ~500 MB |

> **How to download:** open the link above, click the **Download** button on the HuggingFace page, and save the file as `microsoft_Phi-4-mini-instruct-Q6_K.gguf` inside the `model/` folder.

### Why Phi-4-mini?

Older models like Phi-3 use **MHA** — Multi-Head Attention — with 32 key/value heads, which creates a large KV cache of around 804 MB and high RAM usage. Phi-4-mini solves this with two architectural improvements:

* **GQA** — Grouped Query Attention: 8 key/value heads instead of 32, so the KV cache is only around 268 MB.
* **Tied embeddings**: input and output embedding matrices are shared, saving around 600–800 MB.

Combined with **mmap** — memory mapping, where the `.gguf` file stays mostly on disk and only accessed pages load into physical RAM — a 3.16 GB model uses only around 500 MB of real RAM during normal use with short conversations. It runs smoothly on both 8 GB and 16 GB PCs.

Aprende+ limits the model to **2048 tokens of context**. The model supports up to 131,072 tokens, but using the full context would require much more RAM. You will see this message on startup:

```txt
llama_context: n_ctx_seq (2048) < n_ctx_train (131072) -- the full capacity of the model will not be utilized
```

This is **normal and intentional**. The KV cache scales linearly with context size. At 2048 it uses around 268 MB; at 131,072 it would use around 17 GB. For short children's tutoring sessions, 2048 is more than enough and keeps RAM usage low on any PC.

Only keep **one** model in the folder at a time. The first `.gguf` found is loaded automatically. Use the `APRENDEPLUS_MODEL` environment variable to select a specific model by filename substring:

```powershell
set APRENDEPLUS_MODEL=phi    # loads the first .gguf containing "phi" in its name
```

---

## Quick start from source

### Prerequisites

* Python 3.10 or higher
* Node.js 18+ and npm
* **Windows:** Visual Studio 2022 Build Tools, needed to compile `llama-cpp-python`.

```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/aprende-plus.git
cd aprende-plus

# Backend
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/macOS
pip install --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt

# If llama-cpp-python fails to install, see "Building llama-cpp-python" below.

# Frontend
cd chat
npm install
npm run build
cd ..

# Download the model, see Recommended Model above, and place it in model/

# Run
python main.py
```

The app will build the frontend, start the server on `http://127.0.0.1:5050`, and open your browser.

---

## Using a prebuilt release

1. Download the latest `AprendePlus-vX.X.X-win-x64.exe` from the [Releases](https://github.com/YOUR_USERNAME/aprende-plus/releases) page.
2. Create a folder `aprende-plus/` anywhere.
3. Inside it, create a `model/` subfolder.
4. Move the `.exe` into `aprende-plus/`.

```txt
aprende-plus/
├── model/
│   └── microsoft_Phi-4-mini-instruct-Q6_K.gguf
└── AprendePlus.exe
```

5. Download the model file, see [Recommended model](#recommended-model) above, and place it inside `model/`.
6. Run `AprendePlus.exe`.

That's it. No Python, no Node, no dependencies to install.

---

## Building llama-cpp-python for cross-CPU compatibility

The prebuilt `llama-cpp-python` wheels may be compiled with AVX512 instructions, causing an `OSError: [WinError -1073741795]` on CPUs without AVX512 support, such as Intel 12th/13th gen hybrid cores, AMD Ryzen, or older Intel processors.

### Verify your current build

```powershell
python -c "import llama_cpp; print(llama_cpp.llama_print_system_info().decode())"
```

If you see `AVX512 = 1`, your build will crash on non-AVX512 CPUs.

### Step-by-step fix

1. **Download the source**

```powershell
pip download llama-cpp-python --no-deps --no-binary llama-cpp-python -d C:\temp\llama_src
cd C:\temp\llama_src
tar -xf llama_cpp_python-<VERSION>.tar.gz
```

2. **Edit `vendor\llama.cpp\ggml\CMakeLists.txt`**

Change this:

```cmake
set(GGML_NATIVE_DEFAULT ON)
```

To this:

```cmake
set(GGML_NATIVE_DEFAULT OFF)
```

Then change this:

```cmake
if (GGML_NATIVE OR NOT GGML_NATIVE_DEFAULT)
```

To this:

```cmake
if (GGML_NATIVE)
```

3. **Delete precompiled DLLs**

```powershell
Remove-Item "llama_cpp\lib\*" -ErrorAction SilentlyContinue
```

4. **Install from the modified source**

```powershell
pip uninstall llama-cpp-python -y
python -m pip install "C:\temp\llama_src\llama_cpp_python-<VERSION>" --no-cache-dir --no-build-isolation
```

5. **Verify**

```powershell
python -c "import llama_cpp; print(llama_cpp.llama_print_system_info().decode())"
```

Expected result: `AVX2 = 1`, and `AVX512` should be absent.

> **Important:** If you update `llama-cpp-python` to a newer version, repeat these steps from step 1.

---

## Database

Aprende+ uses **SQLite** for persistence. No database server, configuration, or setup is required. The file `aprendeplus_chat.db` is created automatically in the app directory the first time you run it.

### Schema

**`chat_sessions`** — one row per conversation.

| Column          | Type      | Notes                                 |
| --------------- | --------- | ------------------------------------- |
| `session_id`    | TEXT UUID | Primary key                           |
| `user_id`       | TEXT      | Defaults to `"anonymous"`             |
| `title`         | TEXT      | Auto-generated from the first message |
| `created_at`    | TIMESTAMP | Set on creation                       |
| `last_activity` | TIMESTAMP | Updated on every message              |

**`chat_messages`** — individual messages within a session.

| Column         | Type      | Notes                          |
| -------------- | --------- | ------------------------------ |
| `id`           | INTEGER   | Auto-increment primary key     |
| `session_id`   | TEXT      | Foreign key to `chat_sessions` |
| `user_message` | TEXT      | What the user typed            |
| `ai_response`  | TEXT      | What the model replied         |
| `timestamp`    | TIMESTAMP | When it was sent               |

### How it works

1. When you start a new chat, a `session_id` UUID is created and stored in `chat_sessions`.
2. Each exchange, user message plus AI reply, is inserted into `chat_messages`.
3. The sidebar loads session titles and message counts via a `LEFT JOIN` query.
4. Clicking a past session loads its last 6 message pairs and restores the conversation.
5. Deleting a session removes both its row in `chat_sessions` and all related rows in `chat_messages`.

The database is local to your machine and never touched by anything other than Aprende+. No telemetry, no sync, no cloud.

---

## Building the release yourself

To generate the portable `.exe` from source:

```bash
# Make sure the frontend is built
cd chat
npm run build
cd ..

# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller AprendePlus.spec
```

The output goes to `dist/AprendePlus.exe`. Zip that folder, including `model/` and `config/`, and you have a portable release.

---

## Project structure

```txt
aprende-plus/
├── api/                  # FastAPI endpoints
├── chat/                 # Svelte frontend
│   ├── src/              # source files
│   └── dist/             # built output, generated
├── config/               # prompt templates and settings
├── core/                 # LLM engine, prompt building
├── database/             # SQLite chat repository
├── model/                # place your .gguf here
├── schemas/              # Pydantic request/response models
├── utils/                # helpers, input handling, progress
├── main.py               # app entry point
├── config.py             # paths and defaults
└── AprendePlus.spec      # PyInstaller build spec
```

---

## License

MIT
