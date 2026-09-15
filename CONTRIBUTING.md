# Contributing

Contributions should preserve local-first patient privacy, explicit statistical assumptions, and reproducible resource provenance.

```bash
python -m pip install -e '.[test]'
ruff check .
pytest -q
```

New statistical behavior requires a small analytically verifiable test and, where practical, comparison with an independent established implementation. Never commit identifiable patient data. Use synthetic or explicitly redistributable fixtures only.
