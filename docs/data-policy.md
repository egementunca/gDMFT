# Data policy

gDMFT separates project-generated results, large numerical artifacts, external
software, and literature reference data.

## Repository data

Git stores schemas, manifests, checksums, small canonical tables, test
fixtures, and figure recipes. These files are reviewable and sufficient to
identify every published result unambiguously.

## Archived data

Lossless roots, checkpoints, Matsubara and real-frequency functions, spectra,
and large scan tables belong in an immutable versioned archive. Published
manifests record the archive DOI or URI and the checksum of each artifact.

## External software

External implementations are not vendored silently. Each source records:

- repository URL and immutable revision;
- upstream license and citation;
- supported adapter and execution mode;
- environment and output conventions.

Updating an external revision creates a new comparison dataset.

## Reference data

Literature and collaborator-provided tables require a citation, provenance,
unit convention, and redistribution status. When redistribution is not
permitted, the registry stores metadata and retrieval instructions rather
than the original file.

## Required asset metadata

Every registered asset records its ID and version, storage tier, URI, SHA-256,
byte size, media type, schema, generator command, code revision, environment,
parent asset IDs, units, gate semantics, license, and citation.
