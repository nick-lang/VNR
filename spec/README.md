# Spec (`spec/`)

Architecture spec / manifesto drafts. The first real document, `architecture-v0.md`, is written in Phase 3. It is versioned (`-v0`, `-v1`, ...) and updated as experiment results land.

Each component section must include: the design commitment, the strongest prior art it draws on, which `ledger/limitations.md` item it addresses, and explicit kill-criteria ("how this could be wrong").

Components to specify:
- Representation (objects/latents vs tokens)
- Addressable memory model (episodic + working)
- Reasoning core (small recurrent "CPU" / refinement)
- Hypothesis substrate (DSL vs learned latent ops)
- Objective (MDL/energy vs likelihood)
- Test-time learning loop
