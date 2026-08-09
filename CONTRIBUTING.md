# Contributing

Thanks for considering a contribution to AppStoreWebhook.

## Getting started

```bash
git clone https://github.com/kmishukov/AppStoreWebhook.git
cd AppStoreWebhook
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Before opening a PR

Run lint and tests locally — the same checks run in CI:

```bash
ruff check .
ruff format --check .
isort --check-only .
pytest
```

If `ruff` or `isort` report issues, `ruff check --fix .`, `ruff format .`, and `isort .` will fix most of them automatically.

## Making changes

- Keep pull requests focused on a single change.
- Add or update tests for behavior you change.
- Update `README.md` if you change setup, configuration, or endpoints.

## Reporting bugs / requesting features

Please open an issue using the provided templates. Include steps to reproduce for bugs, and the use case for feature requests.
