import os
import subprocess
import sys
import signal

import uvicorn

def _find_python():
    """Find the correct Python from the venv, falling back to sys.executable."""
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python.exe")
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable

if __name__ == "__main__":
    python = _find_python()
    paf_process = None
    try:
        paf_process = subprocess.Popen(
            [python, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        print(f"PAF backend started on port 8001 (PID: {paf_process.pid})")

        reload = os.getenv("RELOAD", "true").lower() == "true"
        uvicorn.run(
            "backend.main:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            reload=reload,
            reload_dirs=["backend"] if reload else None,
        )
    except KeyboardInterrupt:
        pass
    finally:
        if paf_process:
            paf_process.terminate()
            paf_process.wait()
            print("PAF backend stopped")
 