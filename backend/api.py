#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backend/api.py — FastAPI server wrapping the full metre-ba-agent pipeline.

Endpoints:
  POST /extract     — upload PDF -> plan_data.json
  POST /build       — plan_data.json -> metre Excel + comparaison
  POST /report      — summary.json -> rapport PDF
  POST /latex       — summary.json -> rapport LaTeX PDF
  POST /optimise    — metre_lines.json -> Excel optimisation
  POST /pipeline    — run full pipeline (all steps)
  GET  /status      — check pipeline status
  GET  /download/{filename} — download output file

Run: uvicorn backend.api:app --host 127.0.0.1 --port 8765
"""
import asyncio, json, os, shutil, sys, tempfile, uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = FastAPI(title="Metré BA Agent API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

JOBS = {}  # job_id -> {status, progress, outputs, errors}


async def run_pipeline(job_id, pdf_path, ref_path=None, api_key=None,
                       ocr_model=None, latex=False):
    """Run the full pipeline in background."""
    import metre_core
    JOBS[job_id]["status"] = "running"
    JOBS[job_id]["progress"] = "Extraction du plan..."

    try:
        # Step 1: Extract
        from extract_plan import main as extract_main
        sys.argv = ["extract_plan.py", "--pdf", str(pdf_path),
                     "--out", f"output/{job_id}/plan_data.json"]
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            sys.argv.append("--vision")
        if ocr_model:
            sys.argv += ["--ocr", ocr_model]
        os.makedirs(f"output/{job_id}", exist_ok=True)
        # Run in thread to not block
        await asyncio.get_event_loop().run_in_executor(None, extract_main)

        JOBS[job_id]["progress"] = "Génération du métré Excel..."

        # Step 2: Build metre
        from build_metre import main as build_main
        sys.argv = ["build_metre.py",
                     "--plan", f"output/{job_id}/plan_data.json",
                     "--out", f"output/{job_id}/metre_genere.xlsx"]
        if ref_path:
            sys.argv += ["--reference", str(ref_path)]
        await asyncio.get_event_loop().run_in_executor(None, build_main)

        JOBS[job_id]["progress"] = "Génération du rapport PDF..."

        # Step 3: Report
        from build_report import main as report_main
        sys.argv = ["build_report.py",
                     "--summary", "output/summary.json",
                     "--metre", f"output/{job_id}/metre_genere.xlsx",
                     "--out", f"output/{job_id}/rapport_metre.pdf"]
        await asyncio.get_event_loop().run_in_executor(None, report_main)

        JOBS[job_id]["progress"] = "Génération de l'optimisation..."

        # Step 4: Optimisation
        from build_optimisation import main as opt_main
        sys.argv = ["build_optimisation.py",
                     "--lines", "output/metre_lines.json",
                     "--summary", "output/summary.json",
                     "--out", f"output/{job_id}/optimisation.xlsx"]
        await asyncio.get_event_loop().run_in_executor(None, opt_main)

        # Step 5: LaTeX report (if requested)
        if latex:
            JOBS[job_id]["progress"] = "Génération du rapport LaTeX..."
            from backend.latex_report import generate_latex_report
            await asyncio.get_event_loop().run_in_executor(
                None, generate_latex_report, job_id)

        # Collect outputs
        out_dir = Path(f"output/{job_id}")
        outputs = {}
        for f in out_dir.iterdir():
            if f.is_file():
                outputs[f.name] = str(f)
        # Also copy summary/metre_lines
        for f in ["output/summary.json", "output/metre_lines.json",
                  "output/rapport_verification.md"]:
            if os.path.exists(f):
                dest = out_dir / Path(f).name
                shutil.copy2(f, dest)
                outputs[dest.name] = str(dest)

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["progress"] = "Terminé"
        JOBS[job_id]["outputs"] = outputs

        # Load summary for quick access
        if os.path.exists("output/summary.json"):
            JOBS[job_id]["summary"] = json.load(
                open("output/summary.json", encoding="utf-8"))

    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)
        import traceback
        JOBS[job_id]["traceback"] = traceback.format_exc()


@app.post("/pipeline")
async def run_full_pipeline(
    pdf: UploadFile = File(...),
    reference: Optional[UploadFile] = File(None),
    api_key: Optional[str] = Form(None),
    ocr_model: Optional[str] = Form(None),
    latex: bool = Form(False),
):
    """Upload a PDF plan and run the full pipeline."""
    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {"status": "queued", "progress": "En attente..."}

    # Save uploaded files
    work_dir = Path(f"output/{job_id}")
    work_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = work_dir / "plan.pdf"
    with open(pdf_path, "wb") as f:
        f.write(await pdf.read())

    ref_path = None
    if reference:
        ref_path = work_dir / "reference.xlsx"
        with open(ref_path, "wb") as f:
            f.write(await reference.read())

    # Run pipeline in background
    asyncio.create_task(run_pipeline(
        job_id, pdf_path, ref_path, api_key, ocr_model, latex))

    return {"job_id": job_id, "status": "started"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    return JOBS[job_id]


@app.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    fpath = Path(f"output/{job_id}/{filename}")
    if not fpath.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(fpath, filename=filename)


@app.get("/jobs")
async def list_jobs():
    return {jid: {"status": j["status"], "progress": j.get("progress")}
            for jid, j in JOBS.items()}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/install/detect")
async def install_detect():
    """Detect installed components."""
    state = {"components": {}, "python_ok": False, "node_ok": False}
    try:
        import pdfplumber, openpyxl, fitz, yaml, reportlab
        state["components"]["core"] = True
        state["python_ok"] = True
    except ImportError:
        pass
    try:
        import fastapi, uvicorn
        state["components"]["api"] = True
    except ImportError:
        pass
    try:
        import torch, transformers
        state["components"]["vision"] = True
    except ImportError:
        pass
    from pathlib import Path
    if (Path(__file__).resolve().parent.parent / "electron" / "node_modules" / ".package-lock.json").exists():
        state["components"]["electron"] = True
    return state


@app.post("/install/run")
async def install_run(components: list[str] = None):
    """Install selected components."""
    import subprocess, sys
    results = {"success": [], "failed": []}
    for comp in (components or []):
        try:
            if comp == "core":
                subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                    "pdfplumber>=0.11", "PyMuPDF>=1.24", "openpyxl>=3.1", "PyYAML>=6.0", "reportlab>=4.0"],
                    capture_output=True, timeout=300)
            elif comp == "api":
                subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                    "fastapi>=0.115", "uvicorn>=0.34", "python-multipart>=0.0.18"],
                    capture_output=True, timeout=300)
            elif comp == "vision":
                subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                    "transformers>=4.45", "torch>=2.2", "torchvision>=0.17", "accelerate>=0.34"],
                    capture_output=True, timeout=600)
            results["success"].append(comp)
        except Exception as e:
            results["failed"].append({"id": comp, "error": str(e)})
    return results
