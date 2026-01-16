# pretix-opencollective-payment

Open Collective payment provider plugin for pretix.

## Development (uv)

- Create a virtual environment: `uv venv`
- Install dependencies: `uv pip install -e .`
- Add this project to your pretix instance by including `pretix_opencollective` in `INSTALLED_APPS`.
- Run pretix and enable the payment provider in the event settings.
