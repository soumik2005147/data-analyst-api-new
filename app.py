from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from datetime import datetime
import traceback
import os
import json

from pipeline import run_pipeline
from utils import setup_logger

app = FastAPI(title="Data Analyst Agent (Gemini)", version="1.2")

# ---- CORS (allow all; tighten if you have a frontend domain) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["https://your-frontend.example"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Helpers -----------------------------------------------------
def save_to_tempfile(upload: UploadFile) -> str:
    """
    Save an uploaded file to ./tmp with a timestamped name.
    Returns a relative path (string).
    """
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    name, ext = os.path.splitext(upload.filename or "file")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{name}_{timestamp}{ext or ''}"
    abs_path = os.path.join(tmp_dir, safe_name)

    # ensure pointer is at start, then save
    try:
        upload.file.seek(0)
    except Exception:
        pass

    with open(abs_path, "wb") as f:
        f.write(upload.file.read())

    # reset pointer for any later reads
    try:
        upload.file.seek(0)
    except Exception:
        pass

    return os.path.relpath(abs_path, os.getcwd())


def process_attachments(files: List[UploadFile]) -> List[Dict[str, Any]]:
    """
    Build a list of attachment descriptors:
    [
      {
        "filename": "...",
        "content_bytes": b"...",
        "content_type": "text/csv",
        "tmp_path": "tmp/..."
      },
      ...
    ]
    """
    attachments: List[Dict[str, Any]] = []
    for f in files:
        # Read full content (pointer assumed at 0)
        try:
            f.file.seek(0)
        except Exception:
            pass

        contents = f.file.read()
        tmp_path = save_to_tempfile(f)

        attachments.append(
            {
                "filename": f.filename,
                "content_bytes": contents,
                "content_type": f.content_type,
                "tmp_path": tmp_path,
            }
        )

        # reset for safety
        try:
            f.file.seek(0)
        except Exception:
            pass

    return attachments


# ---- Routes ------------------------------------------------------

@app.get("/")
async def read_root():
    """Simple GET root for sanity/health."""
    return {"message": "Hello, world! v1.2"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# NOTE: Some clients/evaluators POST to "/", so accept it and delegate.
@app.post("/")
async def root_post(request: Request):
    return await analyze_task(request)


@app.post("/api/")
async def analyze_task(request: Request):
    """
    Multipart form endpoint.
    Requires a file field named 'questions.txt' containing the task prompt.
    Any additional uploaded files are treated as attachments.
    """
    log, log_path = setup_logger()
    try:
        start_time = datetime.now()

        # Parse multipart form
        form = await request.form()

        # Validate presence of questions.txt
        if "questions.txt" not in form:
            return JSONResponse(
                status_code=400,
                content={"error": "questions.txt is required"},
            )

        qfile = form["questions.txt"]
        if not hasattr(qfile, "filename"):
            return JSONResponse(
                status_code=400,
                content={"error": "questions.txt must be a file"},
            )

        # Read the task description
        contents = await qfile.read()
        try:
            task_description = contents.decode("utf-8").strip()
        except UnicodeDecodeError:
            task_description = contents.decode("latin-1").strip()

        log("\nReceived Task:\n" + (task_description[:1000] + ("..." if len(task_description) > 1000 else "")))

        # Collect other files as attachments (anything except question(s).txt)
        attachment_files: List[UploadFile] = [
            v
            for k, v in form.multi_items()
            if hasattr(v, "filename")
            and v.filename
            and v.filename.lower() not in {"question.txt", "questions.txt"}
        ]
        attachments = process_attachments(attachment_files)

        # Run the pipeline
        answer = run_pipeline(task_description, log, attachments=attachments)

        # Build response
        end_time = datetime.now()
        log("total time taken to process (mins): " + str((end_time - start_time).total_seconds() / 60))

        # Normalize to JSON
        if isinstance(answer, (dict, list)):
            return JSONResponse(content=answer)

        if isinstance(answer, str):
            # If it's JSON text, parse it; else wrap it
            try:
                parsed = json.loads(answer)
                return JSONResponse(content=parsed)
            except json.JSONDecodeError:
                return JSONResponse(content={"output": answer})

        # Fallback
        return JSONResponse(content={"output": str(answer)})

    except Exception as e:
        # Log full traceback for debugging; return safe JSON error
        tb = traceback.format_exc()
        try:
            log(f"Exception: {e}\n{tb}")
        except Exception:
            pass
        return JSONResponse(
            status_code=500,
            content={"error": f"API: error occurred: {str(e)}"},
        )


# If you ever run locally via `python app.py`, this helps:
if __name__ == "__main__":
    # This won't be used on Render (Render injects $PORT and runs your start command)
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
