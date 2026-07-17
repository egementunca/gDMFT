# External comparison sources

Third-party implementations are not copied into the gDMFT source tree.
`sources.toml` records immutable revisions, licenses, citations, and the
planned integration mode. An entry documents a source; it does not imply that
an adapter has already been implemented.

This separation matters scientifically and legally:

- an external implementation is evidence, not the definition of correctness;
- its raw conventions are preserved before normalization;
- adapters record every unit, energy, and observable transformation;
- upstream licenses and citation requirements remain visible;
- updating an external revision creates a new comparison dataset.
