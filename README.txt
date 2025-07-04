# Planned project layout (WIP)

pico-anemometer/
├── .env                # Stores secrets for local development (NOT for git)
├── .gitignore          # Tells git which files to ignore
├── requirements.txt    # Lists your micropython package dependencies
│
├── src/                # ALL code that will be deployed to the Pico
│   ├── main.py         # Your main application logic
│   ├── config.py       # Handles loading configuration/secrets
│   └── lib/            # Libraries/modules you write belong here
│
├── local_dev/          # Mocks and tools for LOCAL development ONLY
│   ├── machine.py      # Your mock machine module
│   └── network.py      # Your mock network module
│
└── scripts/            # Helper scripts for automation
    ├── install_deps.sh # Installs dependencies to the Pico
    └── deploy.sh       # Deploys your source code to the Pico
