$key = "$env:USERPROFILE\.ssh\id_ed25519"
$art = "/workspace/vnr/experiments/poc-vnr-s5-memory/s5_artifacts"
$cmd = "ls $art/job_sel_*.json $art/job_ret_*.json $art/job_selfsel_*.json 2>/dev/null | wc -l; test -f $art/stage5b_summary.json && echo SUMMARY_READY; pgrep -f runpod_queue.py >/dev/null || echo QUEUE_DEAD"
while ($true) {
    $out = ssh -i $key -p 22042 root@194.68.245.201 $cmd 2>$null
    $joined = ($out -join " | ")
    Write-Output "status: done-jobs=$joined / 24"
    if ($joined -match "SUMMARY_READY" -or $joined -match "QUEUE_DEAD") { break }
    Start-Sleep -Seconds 300
}
