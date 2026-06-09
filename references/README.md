# Reference code (`references/`)

Vendored upstream repositories for reuse and reproduction in Phase 4. These are cloned locally and **git-ignored** (not committed to this repo) to avoid bloating history and to respect upstream licenses. Re-clone with the commands below.

| Name | What | Clone |
| --- | --- | --- |
| `NVARC` | ARC Prize 2025 winner: synthetic data + test-time training + ARChitects/TRM ensemble | `git clone --depth 1 https://github.com/1ytic/NVARC references/NVARC` |
| `TinyRecursiveModels` | Tiny Recursive Model (~7M params, ~45% ARC-AGI-1) | `git clone --depth 1 https://github.com/SamsungSAILMontreal/TinyRecursiveModels references/TinyRecursiveModels` |
| `CompressARC` | MDL / compression, zero-pretraining single-puzzle solver | `git clone --depth 1 https://github.com/iliao2345/CompressARC references/CompressARC` |

Notes:
- TRM and CompressARC are the priority reproductions (PoC-A): small and runnable on modest hardware.
- Verify the exact upstream URLs at clone time (forks/renames happen); the canonical pointer is the NVARC repo and the ARC Prize 2025 results page.
- Each upstream keeps its own LICENSE; review before reuse.
