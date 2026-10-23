# Provenance

- canonical: trim-my-output
- mode: composed
- body changed: no (every excerpt verbatim; only headings and ordering are new)
- sources: caveman, superpowers
- spec: compose/trim-my-output.yml
- composed: 2026-10-23

## Excerpts

| upstream skill | section | sha256 | chars |
|---|---|---|---|
| caveman |  | 552fcdcb5b973ee5cdad8ff7bce2b969751484cdea9c033c39b7c72e05bc6f0d | 4418 |
| caveman-compress | ### Remove | 4e38f1fe738b9673861387a9e5f6314fd5f2a9fe3afcb5edfde25b512d653fa9 | 446 |
| caveman-compress | ### Preserve EXACTLY (never modify) | bb86935c932751c724aab9de3bf11f64b4673283137b9552535236ac60a39570 | 471 |
| verification-before-completion | ## The Gate Function | f70207ac270a107ede3ed42c823c67fef49712d93e99cab9665fa54cda938fdc | 429 |


Each sha256 above is over the exact excerpt text. verify.ps1 re-extracts and
re-hashes to prove the shipped body still matches upstream.
