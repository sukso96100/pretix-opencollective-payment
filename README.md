# pretix-opencollective-payment

Open Collective payment provider plugin for pretix.

[Watch plugin demo video on YouTube](https://youtu.be/R6yUZhq6jgU)

## Installation & Configuration
On your pretix setup, with virtualenv activated, run following command to install this plugin.
```bash
pip install git+https://github.com/sukso96100/pretix-opencollective-payment.git
```
You should now be able to see Open Collective payment plugin on your event's plugin settings page. Enable the plugin, then on payment settings page, update following configuration.

- Collective slug (required): slug of your collective on Open Collective. (e.g. https://opencollective.com/ubucon-asia/ -> `ubucon-asia`)
- Event slug (optional): If you want to accept payments for specific event created within your collective, configure this. (e.g. https://opencollective.com/ubucon-asia/events/ubucon-asia-2025-bd8cda5f -> `ubucon-asia-2025-bd8cda5f`)
- Personal token (required): Your personal token obtained from Open Collective.
  - [Learn how to issue personal tokens](https://documentation.opencollective.com/development/personel-tokens)
  - Your personal token should have access to `transactions` scope.
- Use staging (disabled by default): Enable this if you want to redirect users to Staging environment of Open Collective for payment.

> **Note**: Your event's currency setup must match with your collective's base currency. As the plugin and the Open Collective's API this plugin use can't handle amount input with different currency.

## Development setup

Setup your own pretix development environment [following the documentation here/](https://docs.pretix.eu/dev/development/setup.html) Then, Enter Virtual environment of your pretix development instance

```bash
cd pretix
source .venv/bin/activate # or something like source venv/bin/activate depending on your setup
```

On the shell with virtualenv activated, move to parent directory of your pretix setup then clone this reporitory. After that, enter the cloned repo and install the plugin.
```bash
cd ../
git clone https://github.com/sukso96100/pretix-opencollective-payment.git
cd pretix-opencollective-payment
pip install -e .
```

Next, Run your local pretrix instance. You will be able to see Open Collective plugin on each event's plugin settings page. To test your modification, simply run `pip install -e .` with virtualenv activated for your pretix setup and current directory set as this plugin project's root.
