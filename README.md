# pretix-opencollective-payment

Open Collective payment provider plugin for pretix.

## Development (uv)

- Create a virtual environment: `uv venv`
- Install dependencies: `uv pip install -e .`
- Add this project to your pretix instance by including `pretix_opencollective_payment` in `INSTALLED_APPS`.
- Run pretix and enable the payment provider in the event settings.
- Configure the provider with your collective slug, optional event slug, and personal token.
- Enable staging mode if you want to test against Open Collective staging.
- Inform attendees they must click **Continue** on Open Collective's redirect warning after payment.
- Refunds and cancellations must be handled in Open Collective.
