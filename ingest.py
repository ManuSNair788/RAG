"""
ingest.py - Orchestrator for Phase 6 Scheduling

This script simply runs our ingestion pipeline in sequence:
1. Scraper (Downloads HTML)
2. Chunker (Extracts chunks and metadata)
3. Embedder (Embeds and saves to ChromaDB)

This script is meant to be executed daily via GitHub Actions.
"""

import sys
import subprocess

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        print(f"Error: {script_name} failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    print(f"--- Finished {script_name} ---\n")

if __name__ == "__main__":
    print("Starting Daily Data Ingestion Pipeline...")
    
    # 1. Scrape the latest data from the AMCs
    run_script("scraper.py")
    
    # 2. Chunk the new HTML data into JSON semantic chunks
    run_script("chunker.py")
    
    # 3. Embed the chunks and update ChromaDB
    run_script("embedder.py")
    
    print("Daily Data Ingestion Pipeline completed successfully!")
