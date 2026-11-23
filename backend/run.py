#!/usr/bin/env python3
"""
Launcher script for Multilingual Government Scheme & Policy Assistant backend.
"""
import sys
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

def check_dependencies():
    missing = []
    for pkg in ["fastapi", "uvicorn", "pydantic"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"⚠️  Missing required packages: {', '.join(missing)}")
        print("👉 Please install dependencies by running:")
        print("   pip install -r requirements.txt\n")
        return False
    return True

if __name__ == "__main__":
    if not check_dependencies():
        choice = input("Do you want to run 'pip install -r requirements.txt' now? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt")])
        else:
            sys.exit(1)

    import uvicorn
    from app.config import settings

    print(f"🏛️ Starting {settings.PROJECT_NAME} on http://localhost:{settings.PORT}")
    print(f"📖 Swagger API Docs: http://localhost:{settings.PORT}/docs")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
