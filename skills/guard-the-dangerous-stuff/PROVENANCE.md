# Provenance

- canonical: guard-the-dangerous-stuff
- mode: composed
- body changed: no (every excerpt verbatim; only headings and ordering are new)
- sources: gstack, caveman
- spec: compose/guard-the-dangerous-stuff.yml
- composed: 2026-10-23

## Excerpts

| upstream skill | section | sha256 | chars |
|---|---|---|---|
| migration |  | f7c31e0e9f59cd598e54e0c853d978107e62e21029ccc7ab0dc209b6dfbccbec | 559 |
| deprecation-and-migration | ## The Deprecation Decision | bcf3010490169c9151213919bf26cda852095a939546f406c8ee20189cf8f462 | 640 |
| careful | ## What's protected | 64767c8b0aedba6f28e501a5878b6fa9f78a6f2e91b4ebc002300e2aca864397 | 667 |
| careful | ## PowerShell and cmd (Windows) | b7c5bcb1b42d8135e3f93d535e015f4826f35cd744b52cdbb1d5889d71fd2eb0 | 1084 |
| careful | ## Safe exceptions | d29f5f06c335699da907a194259b1d41fd73ce16e68673c164812e6d65e4cef6 | 167 |
| careful | ## HIGH tier (hard deny) | dcfe7589f3e29f7175cf919c64f4e32df6b0b754d0f48445fbd19a1936be532d | 442 |
| careful | ## Project patterns (additive only) | edaf8de1042be573214df41f6a052ce7d59507bd95ab66cf9d7c862b6229b0d5 | 427 |


Each sha256 above is over the exact excerpt text. verify.ps1 re-extracts and
re-hashes to prove the shipped body still matches upstream.
