# Academic Writing Template

Reusable LaTeX starter for German academic reports and theses with `mcidoc`.

## Included structure
- `Main-Report.tex` for reports
- `Main-Thesis.tex` for theses
- `chapter/` for reusable section files
- `img/` for figures and diagrams
- `Sources/` for rules, references, and source material
- `references.bib` for bibliography entries

## Before starting a new project
- Replace all placeholder metadata in the main `.tex` files.
- Remove or rewrite any example text in `chapter/`.
- Add only project-relevant sources and figures.
- Delete build artifacts after compiling.

## Build and automatic cleanup
- Build both documents: `make all`
- Build only report: `make report`
- Build only thesis: `make thesis`
- Build and automatically remove intermediate files (keep PDF): `make report-clean`, `make thesis-clean`, or `make all-clean`
- Remove intermediate files without building: `make clean`
- Remove all generated files including PDFs: `make clean-all`
