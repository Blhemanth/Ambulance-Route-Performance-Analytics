import os
import subprocess
import time

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
browser_exe = chrome_path if os.path.exists(chrome_path) else edge_path

out_dir = os.path.abspath("reports/screenshots")
os.makedirs(out_dir, exist_ok=True)

pages = [
    ("01_dashboard.png", "http://localhost:8501"),
    ("02_route_optimizer.png", "http://localhost:8501/Shortest_Path"),
    ("03_road_explorer.png", "http://localhost:8501/Network_Visualization"),
    ("04_hospital_finder.png", "http://localhost:8501/Hospital_Validation"),
    ("05_analytics.png", "http://localhost:8501/Analytics"),
    ("06_corpus_overview.png", "http://localhost:8501/Overview"),
    ("07_signal_explorer.png", "http://localhost:8501/Dataset_Explorer"),
    ("08_methodology.png", "http://localhost:8501/Methodology")
]

for filename, url in pages:
    target_png = os.path.join(out_dir, filename)
    cmd = [
        browser_exe,
        "--headless=new",
        f"--screenshot={target_png}",
        "--window-size=1440,900",
        "--virtual-time-budget=5000",
        url
    ]
    print(f"Capturing {filename} from {url}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(target_png):
        size_kb = os.path.getsize(target_png) / 1024
        print(f" -> SUCCESS: {filename} ({size_kb:.1f} KB)")
    else:
        print(f" -> FAILED: {filename}. Return code: {res.returncode}. Stderr: {res.stderr[:200]}")

print("\nDone capturing all screenshots!")
