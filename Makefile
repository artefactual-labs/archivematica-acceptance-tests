.PHONY: pip-compile
pip-compile:  # Compile pip requirements
	pip-compile --allow-unsafe --generate-hashes --output-file requirements.txt requirements.in
	pip-compile --allow-unsafe --generate-hashes --output-file requirements-dev.txt requirements-dev.in

.PHONY: pip-upgrade
pip-upgrade:  # Upgrade pip requirements
	pip-compile --allow-unsafe --upgrade --generate-hashes --output-file requirements.txt requirements.in
	pip-compile --allow-unsafe --upgrade --generate-hashes --output-file requirements-dev.txt requirements-dev.in

.PHONY: pip-sync
pip-sync:  # Sync virtualenv
	pip-sync requirements.txt

.PHONY: pip-sync-dev
pip-sync-dev:  # Sync dev virtualenv
	pip-sync requirements-dev.txt
