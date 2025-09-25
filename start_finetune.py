import os
import json
import time
import random
import logging
import argparse
from pathlib import Path
from typing import Optional
import requests

# config
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
API_VERSION = "2023-10-01-preview"
TIMEOUT_DEFAULT = 120

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def validate_jsonl(path: Path) -> bool:
    if not path.exists(): 
        log.error("File not found: %s", path); return False
    ok = True
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line: 
            log.debug("Line %d empty, skip", lineno); continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            log.error("Line %d: JSON error: %s", lineno, e); ok = False; continue
        msgs = obj.get("messages")
        if not isinstance(msgs, list) or len(msgs) != 2:
            got = f"{type(msgs).__name__}/len={len(msgs) if isinstance(msgs, list) else 'N/A'}"
            log.error("Line %d: expected messages list length 2, got %s", lineno, got); ok = False; continue
        roles = {m.get("role") for m in msgs if isinstance(m, dict)}
        if roles != {"user", "assistant"}:
            log.error("Line %d: roles must be user+assistant, found %s", lineno, roles); ok = False
    return ok


def upload_file(session: requests.Session, filepath: Path) -> str:
    url = f"{ENDPOINT}/openai/files?api-version={API_VERSION}"
    with filepath.open("rb") as fh:
        files = {"file": (filepath.name, fh, "application/jsonl")}
        resp = session.post(url, files=files, data={"purpose": "fine-tune"}, timeout=TIMEOUT_DEFAULT)
    resp.raise_for_status()
    j = resp.json()
    return j.get("id") or j.get("fileId") or j.get("file_id") or (_ for _ in ()).throw(RuntimeError("Unexpected upload response: " + json.dumps(j, indent=2)))


def wait_for_processing(session: requests.Session, file_id: str, attempts: int = 40, delay: float = 2.0) -> None:
    url = f"{ENDPOINT}/openai/files/{file_id}?api-version={API_VERSION}"
    for i in range(1, attempts + 1):
        resp = session.get(url, timeout=30); resp.raise_for_status(); j = resp.json()
        status = j.get("status")
        log.info("[%d/%d] status: %s", i, attempts, status)
        if status == "processed": return
        if status in ("failed", "error", "deleted"): raise RuntimeError("File processing failed: " + json.dumps(j, indent=2))
        sleep = min(delay * (1.5 ** (i - 1)), 10.0) + random.uniform(0, 0.5)
        time.sleep(sleep)
    raise TimeoutError("Timeout waiting for file to be processed")


def create_finetune_job(session: requests.Session, training_file_id: str, model: str) -> dict:
    url = f"{ENDPOINT}/openai/fine_tuning/jobs?api-version={API_VERSION}"
    resp = session.post(url, json={"training_file": training_file_id, "model": model}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    p = argparse.ArgumentParser("Upload JSONL and start fine-tune job")
    p.add_argument("-f", "--file", required=True, help="training jsonl path")
    p.add_argument("-m", "--model", default="gpt-35-turbo", help="base model")
    args = p.parse_args()

    if not ENDPOINT or not API_KEY:
        raise SystemExit("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")

    path = Path(args.file)
    log.info("Validating %s", path)
    if not validate_jsonl(path): raise SystemExit("Validation failed")

    session = requests.Session()
    session.headers.update({"api-key": API_KEY, "Content-Type": "application/json"})
    try:
        log.info("Uploading...")
        file_id = upload_file(session, path)
        log.info("Uploaded, id=%s", file_id)

        log.info("Waiting for processing...")
        wait_for_processing(session, file_id)

        log.info("Creating fine-tune job...")
        job = create_finetune_job(session, file_id, args.model)
        log.info("Job created:\n%s", json.dumps(job, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()
