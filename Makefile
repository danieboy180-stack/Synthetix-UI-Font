.PHONY: all build tokens verify clean-check
all: build tokens verify
build:
	python build/build_static.py && python build/build_variable_export.py
tokens:
	python tokens/build_tokens.py
verify:
	python tools/check_regression.py && python tools/run_checks.py && python tools/confusables.py && python tools/engine_parity.py chromium && python tools/contract_check.py
clean-check:
	python tools/check_reproducible.py
