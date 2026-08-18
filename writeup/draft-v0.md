# Weight-Space Memory Fails Three Ways, and Coverage Is a Draw: Pre-Registered Negative Results from a Zero-Pretraining ARC Substrate

> **Status:** draft v0 (2026-08-18). Slots marked `[E1B: ...]` await the
> in-flight capture runs; everything else is backed by banked artifacts in
> this repository. Target venue: ARC Prize paper track / TTU-style workshop.

## Abstract (draft)

Zero-pretraining, per-task-MDL solvers (CompressARC-class) are among the few
ARC approaches whose cost profile matches the field's acknowledged open
problem — the *efficiency* gap. We report a pre-registered experimental
program probing two natural extensions of this substrate: cross-task
weight-space memory and test-time compute allocation. All hypotheses were
pre-registered with numeric accept/kill criteria and committed to a public
git history before each run. Three independent mechanisms for weight-space
memory fail: (1) post-hoc weight averaging transmits but also corrupts
(median warm/cold ratio 1.22; interference losses); (2) retrieval-gated
donor selection finds *nothing reusable* — zero wins across 11 tasks even
though the retrieval probe verifiably works; (3) a jointly trained shared
backbone fails its own validity gate — it cannot re-solve its training
tasks without co-adapted per-task latents, and per-task adaptation deltas
from the shared basin are mutually orthogonal (median pairwise cosine
0.007). Separately, matched-compute restart diversity does not beat longer
convergence (kill), but the experiment surfaced a methodological finding
that outranks the verdict: solve coverage is a stochastic draw. Across 198
cold runs of the unmodified substrate on a fixed 50-task dev split, the
ever-solved set (15 tasks) splits into a deterministic core of 7 and a
stochastic fringe of 8 — the fringe is larger than half the margin — and
same-seed same-hardware runs are not even deterministic (final loss spread
436–571 across seven identical 120-step configs). Single-run solve counts,
including our own baseline's 11/50, are therefore 1-sample mode estimates;
we argue coverage claims in this substrate class must be reported
run-marginalized with stated budgets. Label-free selection — the missing
piece that would convert re-roll coverage into benchmark score under ARC's
pass@2 budget — remains open: two loss-scorer selectors are refuted
(trial-loss probes; tail-mean loss anti-correlates with solving), while
last-step loss and cross-run agreement voting survive a small
retrospective test `[E1B: and a pre-registered capture evaluation]`.

## 1. Introduction

The ARC Prize Foundation's own 2025 assessment splits the field's open
problems in two: the accuracy gap is "bottlenecked by engineering," while
the *efficiency* gap is "bottlenecked by fundamental science and new
ideas" [ARC Prize 2026]. Meanwhile the cost of frontier-*level* capability
is rising 3–18x/yr despite falling per-token prices [Price of Progress
2026], and the living-survey cost law (accuracy ≈ 0.15·log(cost)) prices
brute-force scaling out of the efficiency race [Living Survey 2026].

This motivates study of the one substrate family whose cost floor is
radically different: zero-pretraining per-task solvers (CompressARC, TRM),
which buy their capability at test time from a single consumer GPU. We ask
two questions of this substrate, both pre-registered with numeric
accept/kill rules *before* each run:

1. **Can per-task learning be amortized through weight-space memory?**
   (H9: weight averaging; H10: retrieval-gated donor selection; H14:
   jointly trained shared backbone.)
2. **How should test-time compute be spent, and can a label-free selector
   convert extra samples into score?** (H15: restart diversity at matched
   compute; E1: selector evaluations.)

All five answers are negative or void — and we argue the negatives are
individually informative and jointly map where memory in this substrate
*cannot* live. A sixth, unplanned finding emerged from the program's own
bookkeeping: the substrate's solve coverage is run-stochastic in a way that
undermines single-run benchmark claims, including ours.

**Contributions.**
- Three mechanism-level negatives closing whole-blob weight-space memory
  for independently trained per-task MDL models, with validity gates
  separating "mechanism fails" from "plumbing fails" (§4).
- Evidence that the knowledge in this substrate lives in latent/weight
  *co-adaptation*, not weights alone: a jointly trained backbone cannot
  re-solve its own training tasks with fresh latents (§4.3).
- A delta-geometry readout: per-task adaptation vectors from a shared
  basin are pairwise orthogonal (median cos 0.007) — the null case for
  cross-task transfer (§4.3).
- A 198-run coverage study: the solve set = deterministic core (7) +
  stochastic fringe (8, per-task p̂ 0.25–0.75) + never-solved (35);
  same-seed runs are nondeterministic on consumer hardware; matched-run
  flip rates 18–67% among fringe tasks (§5).
- Refutation of two label-free loss-scorer selectors and a pre-registered
  evaluation of agreement/stability/margin selectors `[E1B: results]`
  (§6).
- The full pre-registration discipline itself: hypotheses, numeric bars,
  and kill decisions committed in advance in a public git history — rare
  in this literature and, we argue, the reason the negatives are legible.

## 2. Substrate and protocol

**Substrate.** Unmodified CompressARC [Liao & Gu 2025]: a ~76K-parameter
model per task, randomly initialized, trained only at test time to
minimize description length; the answer is the modal postprocessed
solution over the training trajectory (top-2 = pass@2). No pretraining, no
dataset, no search.

**Benchmark.** A committed 50-task dev split of ARC-AGI-1 evaluation
tasks (`data/dev_split_arc1.json`), fixed on 2026-06-08 before any neural
run, plus 30-task ARC-AGI-2 probes in the symbolic stages.

**Protocol.** 2000 steps/task for benchmark-grade claims (H8
comparability); 1000 steps for experimental arms after a banked-data
analysis showed all 9 stably-solved tasks stabilize by step 541 (median
222). Pass@2 throughout. Per-step top-2 pick histories define
steps-to-stable-solve (earliest step from which the truth stays in the
top-2).

**Hardware history (a finding in itself, §5).** L40S (cloud, H8) → 6x/5x
A40 pods (H9/H10) → local RTX 5090, torch 2.11+cu128 (H14 onward; the
pinned torch 2.5.1 predates Blackwell — deviation recorded). Cold
baselines were re-run on each hardware change.

**Pre-registration.** Every hypothesis entered `ledger/hypotheses.md` with
accept/kill numbers before its runner was launched; decisions and full
run logs are committed. Validity gates (not decision-bearing) separate
mechanism results from broken plumbing.

**Program cost.** Cloud out-of-pocket for the entire program: ~$105
(H8 $86.31; H9 ~$11.60; H10 ~$6.50); all later stages ran on one consumer
GPU at $0 marginal cost. ~380 GPU-h total across all stages.

## 3. Prior stages in brief (symbolic substrate)

Stage 1 validated library amortization synthetically: a BPE-compressed
macro library cut median search states-to-solution 746 → 228 (~3.3x) at
unchanged solve rate — but the hand-built DSL covered ~2% of real
ARC-AGI-1, and three successive substrate redesigns (whole-grid ops;
object-mapped rules; families + stability guard) died on coverage
(1–4/50; kill criteria fired twice). The neural substrate (H8: unmodified
CompressARC, 11/50 pass@2 on the dev split) strictly superset all
symbolic solves and became the program's baseline. We note the Stage-1
result predates and is consistent with the compute-matched
library-learning critique [Berlot-Attwell 2026]: both arms had identical
budgets and reuse was mechanical (macro calls in the search alphabet).

## 4. Weight-space memory: three independent negatives

### 4.1 H9 — post-hoc weight averaging (kill)

Leave-one-out over the 11 H8-solved tasks: warm-start each task's
transformation weights from the element-wise mean of the other 10 donors
(latents always fresh; the substrate factors cleanly into task-shaped
latents and fixed-shape transformation weights). Validity gate passed:
same-task warm restarts re-solve in 61/151 steps (bar ~200).

Result: median warm/cold steps-to-stable-solve ratio **1.222** (accept
needed ≤0.5; kill ≥1.0), retention **8/11** (kill ≤8), probes on unsolved
tasks 0/5. The heterogeneity is the finding: two tasks cold-solves never
solved warm (00576224: 222→∞; d2acf2cb: 517→∞), while others won big
(6df30ad6: 0.31x; 903d1b4a: 0.57x; cd3c21df cold-failed → warm-solved at
749). Transferable structure exists; averaging both transmits and
corrupts.

### 4.2 H10 — retrieval-gated donor selection (kill; zero wins)

If averaging smears, address instead: a trial-loss probe (100 steps per
candidate donor, identically seeded) selects ONE donor to warm-start
from. Validity gate passed — self-retrieval ranked each task's own donor
#1 with clear margin (1210 vs 1336 runner-up; 1338 vs 1616) — so the
probe signal is real.

Result: median ratio **1.396**, retention **7/11** — worse than the soup
on both numbers, and **zero wins**: not one of 11 tasks trained faster
from its best-fitting foreign donor than from random init (worst case
25.8x slower: 62→1599; two cold-solves never solved warm). Selection
collapsed onto "universal donors" (one donor chosen by 6/11 tasks) rather
than task families; the probe measures generic adaptability, not task
similarity. Combined H9+H10 inference: the soup's wins were a property of
*averaging* (distributed regularization), not of any donor's content —
whole trained models are the wrong unit of memory, and no addressing
scheme over monoliths can fix that.

### 4.3 H14 — jointly trained shared backbone (void; the void is the finding)

The merging literature's escape route [Git Re-Basin 2022; merging study
2025]: independently trained nets sit in permutation-distinct basins, so
create the shared structure *during* training — one set of transformation
weights aliased across 6 tasks (per-task latents separate), round-robin,
3 folds over the 9 stably-solvable tasks.

The pre-registered validity gate **failed 3/3**: no backbone re-solved a
task it was itself trained on (fresh latents, 600-step budget, bar ~200)
— while the same tasks *did* solve during joint training (e.g. 4/6 in
fold 1), and the transfer plumbing passed independent round-trip smokes.
The mechanism itself is isolated: **the shared weights, without their
co-adapted latents, do not encode the solutions.** Knowledge in this
substrate lives in latent/weight co-adaptation, not in weights alone.
(Descriptively: warm-starting from the backbone was *slower* than random
init on all 9 tasks, median ratio 3.436.)

The delta-geometry readout sharpens this: per-task fine-tuning deltas
from the same fold backbone are pairwise orthogonal — median cosine
0.0067 (range −0.014 to 0.062) at near-identical norms (~114–121). Even
from a forced shared basin, task adaptations share no direction. In
merging-literature terms this is the good case for interference-free
*merging* and the null case for *transfer*: there is nothing shared to
amortize across these tasks at this scale.

### 4.4 What survives

Three negatives triangulate: averaging corrupts (H9), content-addressing
finds nothing reusable (H10), and joint training stores knowledge
somewhere weights alone cannot carry (H14). What survives is
concept-granularity memory outside the weight blob: the program's own
Stage-1 symbolic macro library (accepted, compute-matched), and the
independent convergence of ArcMemo's concept-level-beats-instance-level
result [ArcMemo 2025] and Pang's growing-library ARC system [Pang 2025].
Parts, not blobs.

## 5. Coverage is a draw, not a set

### 5.1 H15 — restart diversity at matched compute (kill)

On the 39 H8-unsolved dev tasks: arm A = 1×2000 steps (seed 0) vs arm B =
2×1000 steps (seeds 1, 2) with tail-loss selection, matched compute.
Result: A 3/39, B 2/39 → kill. The union-of-B oracle ties A (3), so even
a perfect selector only equals longer convergence: no compute-allocation
free lunch on this axis. (The 2026 matched-compute TTA result suggests we
tested the wrong diversity axis — input augmentation, not init/seed
[TTA 2026]; this is pre-registered as future H16, §7.)

### 5.2 The 198-run coverage study

The program's banked cold runs (H8 50; H9 11; H14 11; H15 126 `[E1B: +34]`)
form an unplanned but well-controlled coverage corpus over the fixed dev
split:

- **Union timeline:** 11/50 (H8, single seed) → 15/50 after H15's
  re-rolls — +36% coverage from protocol-identical re-runs alone.
- **Core/fringe split (tasks with ≥3 runs):** always-solved **7**,
  fractional **8** (p̂ from 0.25 to 0.75), never-solved **35**. The
  stochastic fringe outnumbers the deterministic margin of the core.
- **Matched-group flip rates:** cross-hardware @2000 (L40S vs A40, 11
  solved tasks): 2/11 flips; cross-seed @1000 on solved tasks: 2/9;
  cross-seed @1000 among fringe: 2/3; cross-hardware @2000 on unsolved
  tasks: all 3 arm-A solves are tasks the identical-protocol H8 run did
  not solve.
- **Same-seed nondeterminism:** seven identical 120-step configs (same
  task, seed, hardware, torch) spread final loss 436–571. A fixed seed
  does not pin the trajectory on consumer hardware (CUDA kernel
  nondeterminism compounds over steps). "Seed-stochastic" understates the
  case: coverage is **run**-stochastic. `[E1B: same-config S6-vs-rerun
  flip readout across 30 duplicated configs]`

### 5.3 Consequence for benchmark claims

A single-run solve count in this substrate class is a 1-sample estimate
of the mode of a per-task Bernoulli field. The certified-self-consistency
frame [2510.17472] makes this precise: majority voting is mode
estimation, and certifying the mode needs a sample budget scaled by the
vote margin. We therefore report, and argue others should report:
per-task solve probabilities with run budgets (our Table: 198 runs), not
single-run sets. Our own headline baseline "11/50" is, honestly stated,
"11–15/50 depending on the draw, p̂ per task in Table N."

## 6. Label-free selection: what's refuted, what's live

ARC's pass@2 budget makes re-roll coverage worthless without a label-free
selector. The program has now refuted two scorer-style selectors:

- **Trial-loss probes** (H10): 100-step warm-up loss ranks donors by
  generic adaptability, not task fit; selection collapsed onto universal
  donors.
- **Tail-mean loss** (H15): in 3 of 4 solve cases the solving run had the
  *higher* tail loss; selection accuracy 1/2. Refuted, and consistent
  with H10: smoothed loss level carries no task-relevant signal.

A retrospective re-analysis of all banked runs (E1-A) found the corpus
supports only loss scorers and holds just 8 informative selector cases —
itself a lesson in what to bank — but within them, **last-step loss
picked the solver 6/8** (vs tail-mean 4/6), including both matched-budget
pairs the tail-mean got wrong. The hypothesis-elimination framing
[Transduction 2025] and the matched-compute TTA result [TTA 2026] both
point away from scoring and toward *agreement across candidates*:
candidates form a finite hypothesis class over their outputs, and
disagreement, not loss, is the label-free signal.

`[E1B: pre-registered capture evaluation — final_loss vs vote-margin vs
pick-stability vs cross-run agreement voting, with a never-solved
precision arm measuring agreement's wrong-modal (false-positive) rate.
34 fresh runs banking full pick histories, top-2 grids, and vote
margins. Results land here.]`

## 7. Limitations and live hypotheses

- **One substrate.** All negatives are mechanism-level results *in
  CompressARC-class models*; TRM-family substrates with pretrained priors
  may amortize differently (their TTA works but needs the prior [TRM-TTA
  2025]).
- **Scale.** 11 donor tasks is small; the delta-orthogonality readout
  (§4.3) is the strongest hedge — it predicts the negative would persist
  at moderate scale, but does not rule out family-structured corpora.
- **The efficiency ceiling.** The substrate's absolute score (11–15/50 on
  our dev split; ~20–30% published ARC-1) is far below LLM-dependent
  systems (Pang 77% at ~$4/task); our results say nothing about closing
  that gap, only about which cheap mechanisms do not.
- **Live, pre-registered next:** H16 — augmentation-voting (exact D8 ×
  color-permutation input transforms, reverse-mapped and voted) at
  matched compute, gated on an equivariance smoke (if the architecture is
  effectively D8/color-equivariant, augmentation collapses into seed
  diversity and inherits H15's kill). Voting-with-certificates [2510.17472]
  supplies the stopping rule; ArcMemo-style concept memory remains the
  surviving memory route.

## 8. Conclusion

In a zero-pretraining per-task MDL substrate: memory is not in the
weights — not by averaging, not by addressing, not by joint training;
what the weights "know" they know only together with their co-adapted
latents, and per-task adaptations share no common direction. Test-time
compute buys coverage only stochastically, and the coverage it buys is
invisible to the loss-based selectors this literature (and our own
earlier stages) reached for first. The honest unit of report for this
substrate class is the run-marginalized solve probability, and the honest
open problem — unchanged since the field named it — is a label-free way
to keep what the draws find.

---

### Appendix A — pre-registered decision rules and outcomes (from `ledger/hypotheses.md`)

| Hyp | Mechanism | Accept bar | Kill bar | Outcome |
| --- | --- | --- | --- | --- |
| H5 | symbolic macro library | ≥2x search efficiency | — | ACCEPT (3.3x, synthetic) |
| H7/v2/v3 | hand-built substrates | ≥5/50 | ≤2/50 or no gain | KILL / INCONCLUSIVE / KILL |
| H8 | CompressARC baseline | ≥5/50 & ≥4x raw | ≤2/50 | ACCEPT (11/50) |
| H9 | weight-soup memory | ratio ≤0.5 & ret ≥10/11 | ratio ≥1.0 or ret ≤8/11 | KILL (1.222, 8/11) |
| H10 | retrieval-gated memory | same | same | KILL (1.396, 7/11, 0 wins) |
| H14 | joint shared backbone | ratio ≤0.5 & ret ≥8/9 | ratio ≥1.0 or ret ≤7/9 | VOID (validity gate 0/3) |
| H15 | restart diversity + MDL sel. | B ≥ A+2 & B ≥2 | B ≤ A | KILL (2 vs 3) |

### Appendix B — per-task solve probabilities (198 cold runs)

See `experiments/poc-vnr-s6-ttc/coverage_analysis.json`; fractional tasks:
00576224 3/4, 6df30ad6 3/4, 73182012 2/4, be03b35f 2/4, e66aafb8 2/4,
15663ba9 1/3, cd3c21df 1/3, 981571dc 1/4. `[E1B: refresh with +34 runs]`

### Appendix C — reproducibility

All runners, artifacts, pre-registrations, and this draft are committed at
each decision point; the git history is the lab notebook. Worker-count and
throughput benchmarks for the reference consumer GPU are recorded in
`experiments/poc-vnr-s6-ttc/e1b_runner.py`.
