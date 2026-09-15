# Security and privacy

## Data handling

- Analysis is local by default.
- The GUI binds only to `127.0.0.1` and uses a random access token in its URL.
- The report uses no remote scripts, fonts, analytics, or tracking pixels.
- Raw GUI uploads are removed after a successful analysis.
- Outputs can contain sample identifiers and variant details and must be protected like the source data.
- `download-resources` contacts only the documented public annotation sources and does not read or transmit analysis inputs.

## Reporting a vulnerability

Please report security concerns privately to the repository owner rather than opening a public issue containing patient information. Do not attach real patient files to an issue.

## Clinical status

CMHS VarEnrich is research software and is not validated as a medical device or for diagnostic decision-making. Public database assertions are not independently verified by this software.
