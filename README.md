# pretix-opencollective-payment

Open Collective payment provider plugin for pretix.

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
