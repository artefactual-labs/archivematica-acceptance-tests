UV ?= uv
DOCKER ?= docker
DOCKER_IMAGE ?= archivematica-acceptance-tests:latest
PYTHON_VERSION ?= 3.10
BEHAVE_ARGS ?=

.PHONY: lock
lock:  # Update the lockfile without upgrading locked dependencies
	$(UV) lock

.PHONY: lock-check
lock-check:  # Verify that the lockfile is up to date
	$(UV) lock --check

.PHONY: upgrade
upgrade:  # Upgrade all locked dependencies
	$(UV) lock --upgrade

.PHONY: sync
sync:  # Sync the project and development dependencies
	$(UV) sync --locked

.PHONY: sync-runtime
sync-runtime:  # Sync only the runtime dependencies
	$(UV) sync --locked --no-dev

.PHONY: lint
lint:  # Run all pre-commit checks
	$(UV) run --locked pre-commit run --all-files --show-diff-on-failure

.PHONY: check
check: lock-check lint  # Verify the lockfile and run all checks

.PHONY: behave
behave:  # Run the acceptance tests; pass options with BEHAVE_ARGS
	$(UV) run --locked --no-dev behave $(BEHAVE_ARGS)

.PHONY: smoke-test
smoke-test:  # Run the browser smoke test
	$(UV) run --locked --no-dev python simplebrowsertest.py

.PHONY: docker-build
docker-build:  # Build the test image
	$(DOCKER) build \
		--target archivematica-acceptance-tests \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--tag $(DOCKER_IMAGE) \
		.
