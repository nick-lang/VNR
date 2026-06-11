"""VNR Stage 5 (H9) — multi-GPU queue dispatcher for a RunPod pod.

Runs the same pre-registered job list as local_runner.py, but fans ready jobs
out across all visible GPUs (one job per GPU, dependencies respected, every
result banked to s5_artifacts/ the moment it lands). Safe to kill and re-run;
finished jobs are never recomputed. Failed jobs are retried twice.

Usage (on the pod):
  python experiments/poc-vnr-s5-memory/runpod_queue.py            # all GPUs
  python experiments/poc-vnr-s5-memory/runpod_queue.py --gpus 4
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

LOGS = HERE / "s5_gpu_logs"
MAX_ATTEMPTS = 3


def n_gpus() -> int:
    try:
        out = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, check=True)
        return len([ln for ln in out.stdout.splitlines() if ln.startswith("GPU ")])
    except Exception:
        return 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpus", type=int, default=0, help="0 = autodetect")
    ap.add_argument("--stage", default="5", choices=["5", "5b"])
    args = ap.parse_args()
    gpus = args.gpus or n_gpus()

    if args.stage == "5b":
        import s5b_runner as runner
    else:
        import local_runner as runner
    global done_jobs, job_list, summarize, ARTIFACTS
    done_jobs, job_list, summarize = runner.done_jobs, runner.job_list, runner.summarize
    ARTIFACTS = runner.ARTIFACTS
    runner_script = HERE / ("s5b_runner.py" if args.stage == "5b" else "local_runner.py")

    ARTIFACTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    jobs = job_list()
    attempts: dict[str, int] = {}
    running: dict[str, tuple[subprocess.Popen, int]] = {}
    free = list(range(gpus))
    t0 = time.time()
    print(f"dispatching {len(jobs)} jobs across {gpus} GPUs", flush=True)

    while True:
        done = done_jobs()

        for name, (proc, gpu) in list(running.items()):
            if proc.poll() is None:
                continue
            del running[name]
            free.append(gpu)
            if name in done_jobs():
                print(f"[done {len(done_jobs())}/{len(jobs)}] {name} "
                      f"(t+{(time.time() - t0) / 60:.0f}m)", flush=True)
            else:
                print(f"[FAILED attempt {attempts[name]}] {name} "
                      f"(see s5_gpu_logs/{name}.log)", flush=True)

        done = done_jobs()
        ready = [
            j for j in jobs
            if j["name"] not in done
            and j["name"] not in running
            and attempts.get(j["name"], 0) < MAX_ATTEMPTS
            and all(n in done for n in j.get("needs", []))
        ]
        while free and ready:
            job = ready.pop(0)
            gpu = free.pop(0)
            attempts[job["name"]] = attempts.get(job["name"], 0) + 1
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
            log = open(LOGS / f"{job['name']}.log", "a")
            proc = subprocess.Popen(
                [sys.executable, str(runner_script), "--only", job["name"]],
                env=env, stdout=log, stderr=subprocess.STDOUT,
            )
            running[job["name"]] = (proc, gpu)
            print(f"[launch gpu{gpu}] {job['name']}", flush=True)

        if not running and not ready:
            break
        time.sleep(15)

    done = done_jobs()
    summary = summarize(done)
    out_name = "stage5b_summary.json" if args.stage == "5b" else "stage5_local_summary.json"
    (HERE / out_name).write_text(json.dumps(summary, indent=2))
    failed = [j["name"] for j in jobs if j["name"] not in done]
    print(json.dumps(summary, indent=2))
    if failed:
        print(f"UNFINISHED after {MAX_ATTEMPTS} attempts: {failed}", flush=True)
    print(f"total wall: {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
