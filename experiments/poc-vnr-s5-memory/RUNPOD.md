# Running Stage 5 (H9) on RunPod

The whole experiment (11 cold + 2 sanity + 11 LOO + 5 probe = 29 jobs,
2000 steps each) fans out across one multi-GPU pod via `runpod_queue.py`.
Expected on 8x RTX 4090: ~3-5 h wall, ~$10-15 total (community pricing).

## Owner steps (once, ~5 min)

1. Create an account at [runpod.io](https://www.runpod.io) and add ~$20 credit
   (Billing -> Add funds; prepaid, no subscription).
2. Deploy a pod: **Pods -> Deploy**, pick
   - GPU: **RTX 4090**, count **8** (4 also works; ~2x the wall clock)
   - Cloud type: **Community** (cheapest; this workload checkpoints every job,
     so a rare interruption costs at most one task)
   - Template: any **PyTorch** template (we install our own torch anyway)
   - Disk: 40 GB container disk is plenty
3. When it's running, copy the **SSH command** from the pod's Connect panel
   (looks like `ssh root@<ip> -p <port> -i ~/.ssh/id_ed25519`) and paste it
   into the chat.

## What the agent does from there (scripted)

```powershell
# 1. bundle the needed files (repo-relative layout preserved)
Compress-Archive -Force -DestinationPath vnr_s5_bundle.zip -Path `
  references/CompressARC, experiments/poc-vnr-s5-memory

# 2. ship + unpack + install on the pod
scp -P <port> vnr_s5_bundle.zip root@<ip>:/workspace/
ssh -p <port> root@<ip> "cd /workspace && unzip -q vnr_s5_bundle.zip -d vnr && pip -q install torch==2.5.1 numpy==2.2.2 tqdm==4.66.6 matplotlib==3.10.0"

# 3. launch the queue (nohup survives SSH disconnects)
ssh -p <port> root@<ip> "cd /workspace/vnr && nohup python experiments/poc-vnr-s5-memory/runpod_queue.py > queue.log 2>&1 &"

# 4. poll status / fetch results
ssh -p <port> root@<ip> "cd /workspace/vnr && python experiments/poc-vnr-s5-memory/local_runner.py --status"
scp -P <port> -r root@<ip>:/workspace/vnr/experiments/poc-vnr-s5-memory/s5_artifacts ./experiments/poc-vnr-s5-memory/
scp -P <port> root@<ip>:/workspace/vnr/experiments/poc-vnr-s5-memory/stage5_local_summary.json ./experiments/poc-vnr-s5-memory/
```

**Remember to STOP/TERMINATE the pod when the run is done** — billing is
per-second while it exists. The fetched `s5_artifacts/` + summary are all we
need; the pod is disposable.

## Protocol notes (for the ledger)

- Same pre-registered job list and decision rule as the local runner; only
  the hardware/orchestration changes. Both arms (cold and warm) run on the
  same pod => same-hardware comparison preserved.
- If the pod dies mid-run, redeploy, re-ship, re-launch: banked jobs in
  `s5_artifacts/` carry over (copy them up first) and nothing is recomputed.
