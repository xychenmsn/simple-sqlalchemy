#!/usr/bin/env python3
"""
Documentation build script for Simple SQLAlchemy

This script builds the documentation using Sphinx and can optionally serve it locally.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    
    return result


def install_dependencies():
    """Install documentation dependencies"""
    print("Installing documentation dependencies...")
    
    # Install the package itself
    run_command([sys.executable, "-m", "pip", "install", "-e", "."])
    
    # Install documentation requirements
    docs_req = Path("docs/requirements.txt")
    if docs_req.exists():
        run_command([sys.executable, "-m", "pip", "install", "-r", str(docs_req)])
    else:
        # Fallback to basic requirements
        run_command([
            sys.executable, "-m", "pip", "install",
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0", 
            "myst-parser>=0.18.0"
        ])


def build_docs(clean=False):
    """Build the documentation"""
    docs_dir = Path("docs")
    
    if not docs_dir.exists():
        print("Error: docs directory not found")
        sys.exit(1)
    
    print("Building documentation...")
    
    if clean:
        print("Cleaning previous build...")
        run_command(["make", "clean"], cwd=docs_dir)
    
    # Build HTML documentation
    run_command(["make", "html"], cwd=docs_dir)
    
    build_dir = docs_dir / "_build" / "html"
    if build_dir.exists():
        print(f"✅ Documentation built successfully!")
        print(f"📁 Output directory: {build_dir.absolute()}")
        print(f"🌐 Open: {build_dir / 'index.html'}")
        return build_dir
    else:
        print("❌ Documentation build failed - output directory not found")
        sys.exit(1)


def serve_docs(build_dir, port=8000):
    """Serve documentation locally"""
    print(f"Serving documentation at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        run_command([
            sys.executable, "-m", "http.server", str(port)
        ], cwd=build_dir)
    except KeyboardInterrupt:
        print("\n📡 Server stopped")


def main():
    parser = argparse.ArgumentParser(description="Build Simple SQLAlchemy documentation")
    parser.add_argument("--clean", action="store_true", help="Clean previous build")
    parser.add_argument("--serve", action="store_true", help="Serve documentation locally")
    parser.add_argument("--port", type=int, default=8000, help="Port for local server")
    parser.add_argument("--no-install", action="store_true", help="Skip dependency installation")
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🔨 Building Simple SQLAlchemy Documentation")
    print(f"📁 Project root: {project_root.absolute()}")
    
    # Install dependencies
    if not args.no_install:
        install_dependencies()
    
    # Build documentation
    build_dir = build_docs(clean=args.clean)
    
    # Serve if requested
    if args.serve:
        serve_docs(build_dir, args.port)


if __name__ == "__main__":
    main()
