# Working paper

**From Price Information to Maker Decisions in BTC Five-Minute Markets**\
Eren Ege Çelik - working draft v0.3, 14 September 2026

[Read the manuscript](manuscript.md) / [Download PDF](crypto-working-paper.pdf)

The central question is what maker value remains from observed BTC price information after
order activation, queue access and inventory are included. The draft follows that question through
pricing estimation, measured book response, joint-fill EV and historical policy comparisons.
Implementation versions and campaign details are preserved in Appendix C.

This draft is hosted for reading and methodological feedback. It has not been submitted to a
journal or peer reviewed. Formal submission will be considered after author review and feedback.

## Evidence and version

The technical evidence baseline is
[`6db0102`](https://github.com/ErenEgeCelik/btc-5m-market-microstructure/tree/6db010205b3aa3b8b4ee1d5715e06c47de8023b7).
That release passed 126 tests, 14 example/audit invocations and 19 input hash checks in a clean
checkout. The paper release changes exposition, figures and document generation; it retains
the baseline's research code, tests and data.

Table 3 refits seven fixed specifications on all 358 published feature records. Table 6 and
Figure 3 recompute paired differences and intervals from all 368 matched simulator-output slots.
D4 figure points and D12 decision evidence use stored summaries. Other historical results are
labeled as archived reports. None of the document commands reconstruct unpublished raw tapes.

Version 0.2 expands the earlier draft with the integrated pricing, mechanics and policy methods,
three source-linked figures, binary-risk derivations and related literature, including Semenas
(2026). Publication additions and corrections are distinguished from historical implementations.

Version 0.3 gives the abstract, introduction and conclusion one research question, moves supporting
implementation history into an appendix, and uses [Latin Modern Roman](fonts/README.md), based on
Computer Modern, for classical mathematical-paper typography. Empirical inputs and estimates are
unchanged. The font files are bundled with their upstream license, so no system-font installation
is needed for document generation.

## Rebuild the figures and PDF

Core research examples need only Python's standard library. Document generation additionally uses
Node.js 18+, the locked npm packages in this directory, matplotlib, Python Playwright and Chromium.
Run from the repository root:

```bash
python -m pip install matplotlib playwright
npm ci --prefix paper --ignore-scripts
python -m playwright install chromium
python -B paper/build_figures.py
python -B paper/build_pdf.py
```

The default PDF output is `paper/crypto-working-paper.pdf`. To preserve the distributed file while
building a local copy, pass `--output /path/to/crypto-working-paper.pdf`. An installed compatible
npm directory and Chromium executable can be supplied through `--modules-root` and
`--browser-executable`, respectively. The build itself uses local assets and makes no network
requests. Installation commands download the listed open-source dependencies.

The figure builder checks frozen input hashes, calls the existing public estimators and writes
[figure_manifest.json](figure_manifest.json). The manifest contains figure values, sample sizes,
units, methods and input/output fingerprints. Plot pixel hashes can vary with matplotlib, fonts
and platform; the selected inputs and numerical calculations remain independently inspectable.
The PDF build checks math rendering, image loading and page overflow, and emits local HTML and
a `.build.json` diagnostic beside its output. Those intermediate files are ignored by Git.
Inspect the rendered pages after changes; successful compilation alone is not a layout review.

## Feedback

The most useful feedback concerns implied-scale identification, feature availability, queue
censoring, quantity-aware fill modeling and causal reconstruction of decision times. Every
empirical section identifies its sampling unit and whether the public package recomputes the
result or only audits an archived summary. Related-paper returns are not used as a performance
benchmark across different samples or execution assumptions.
