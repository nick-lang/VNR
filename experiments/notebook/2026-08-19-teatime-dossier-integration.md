# 2026-08-19 — Review + integration of the teatime discovery dossier

- **PoC:** none (reading + vetting, $0; E1-B final 6 jobs restarted in parallel)
- **Hypothesis:** design inputs to H18 (Stage 9b); no decision rule changes
- **Hardware:** n/a

## Setup

Owner ran a separate discovery project (`teatime`, ~11.5k-work corpus around the
abstraction-library question) and asked for a review of its dossier
(`Documents/teatime/DISCOVERIES-VNR.md`): finish the in-flight E1-B runs or pivot,
and if the discoveries are viable, add their full weight to the documented path.

## Vetting (done before integrating; dossier treated as leads, not authority)

- Kashtan & Alon PNAS 2005 (modularly varying goals): characterization matches
  the known paper — modularity does not evolve under fixed OR randomly varying
  goals; emerges rapidly under goals that vary while sharing subgoals; MVG
  systems generalize to unseen related goals. VERIFIED against knowledge.
- Minton 1988 utility problem + CBR case-base maintenance: real, correctly
  characterized (learned macros can slow solvers; retention = cost-benefit
  accounting; CBR maintenance = the "when does adding a case hurt" literature).
  VERIFIED against knowledge.
- arXiv 2405.06399: fetched — confirmed ILP-for-ARC (object-centric DSL as
  background knowledge). arXiv 2411.02272: fetched — confirmed (induction and
  transduction solve DIFFERENT ARC subsets; ensembling approaches human level).

## Verdicts

1. **Treasure 1 (MVG curriculum): VIABLE, integrated.** Two roles:
   (a) retroactive frame — our H14 delta-orthogonality is the MVG null case
   observed in the wild (a handful of arbitrary dev tasks = randomly varying
   goals, exactly the regime where no shared structure forms); the weight-space
   negatives now have a curriculum-theoretic explanation, not just a description.
   (b) forward design — H18 gains a pre-registerable curriculum arm: fixed vs
   shuffled vs modularly-varying re-arc task streams; measure abstraction reuse
   and held-out compositional transfer. Composability as a property of the
   CURRICULUM is a testable, novel-in-this-context claim.
2. **Treasure 2 (utility problem / CBR maintenance): VIABLE, integrated.** It is
   the named, 35-year-old form of the program's own question ("help vs bloat"),
   with a worked playbook (selective retention, utility validation, forgetting).
   H18's curation metric should be Minton-style utility accounting; our Stage-1
   harness already logs the reuse counts the accounting needs. Also strengthens
   the write-up's library discussion (the 2026 compute-matched critique is this
   lineage rediscovered). Open transfer question flagged in the note: "match
   cost" needs a definition for latent-space libraries.
3. **Direction 3 (grammatical-inference bounds): NOT actionable now.** Tracked
   as long-horizon theory in the index; ILPAR + induction/transduction links
   added to the tracked list (the latter independently echoes our portfolio/
   churn finding and may deserve a full note later).

## Integration (this commit)

- `lit/2005-kashtan-alon-mvg.md`, `lit/1988-minton-utility-problem.md` (marked
  as dossier imports with verification status), index entries, tracked-unread
  additions, and the H18 checklist item amended with both design inputs.
- The current write-up and E1-B/H16 path are UNCHANGED: the dossier's weight
  lands on Stage 9's design (still awaiting owner go/no-go), not on the
  in-flight experiments.

## Decision

- E1-B: FINISH, not pivot (6 jobs / ~2 h remained; workers restarted 2026-08-19).
- Dossier: integrated as above. If the owner approves Stage 9, H18's
  pre-registration should name the MVG curriculum arm and utility-accounting
  curation explicitly; draft bars remain the owner's call.
