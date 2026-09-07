from __future__ import annotations
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Sequence

logger = logging.getLogger(__name__)


class ExternalProcessError(RuntimeError):
    pass


def run_pdflatex(
    tex_file: str | os.PathLike[str],
    timeout: int = 30,
    output_dir: Optional[str | os.PathLike[str]] = None,
) -> Path:
    tex_path = Path(tex_file).resolve()
    if not tex_path.is_file():
        raise FileNotFoundError(f"Fichier LaTeX introuvable : {tex_path}")
    working_dir = Path(output_dir).resolve() if output_dir else tex_path.parent
    working_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-no-shell-escape",
        f"-output-directory={working_dir}",
        str(tex_path),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(working_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExternalProcessError(f"Compilation LaTeX expirée (> {timeout}s)") from exc
    except FileNotFoundError as exc:
        raise ExternalProcessError("pdflatex introuvable dans le PATH.") from exc

    pdf_path = working_dir / f"{tex_path.stem}.pdf"
    if not pdf_path.is_file():
        raise ExternalProcessError(f"Échec pdflatex (code {completed.returncode}):\n{completed.stdout[-2000:]}")
    return pdf_path