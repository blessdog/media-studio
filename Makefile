# media-studio — the gate.
#
# Nothing in this repo ran its own tests until 2026-08-03. Eight test files
# existed and were executed only when someone remembered, which is why AGENTS.md
# drifted two tools and fourteen flags in a day. `make check` is now the single
# entry point, and .githooks/pre-commit refuses commits that break it.
#
#   make hooks       once per clone — installs the pre-commit gate
#   make check       offline gate; what the hook runs; needs no Resolve
#   make check-live  full suite; needs Resolve OPEN with no modal dialog
#
# OFFLINE and LIVE together must list every tests/test_*.py — tests/test_docs.py
# asserts that, so a new test cannot be silently left out of the gate.

PY := .venv/bin/python

OFFLINE := tests/test_docs.py \
           tests/test_ableton.py \
           tests/test_bongpot.py \
           tests/test_forge.py \
           tests/test_forge4.py \
           tests/test_registry.py

# Live tests drive Resolve. AGENTS.md §Hard doctrine: if GetCurrentPage()
# returns None a modal dialog holds the UI and every result is void.
LIVE := tests/test_compile.py \
        tests/test_assembly.py

.PHONY: help check check-live hooks worktree worktree-list worktree-rm

help:
	@printf 'make hooks             install the pre-commit gate (once per checkout)\n'
	@printf 'make check             offline gate — docs contract + unit tests\n'
	@printf 'make check-live        full suite — needs Resolve open, no modal dialog\n'
	@printf 'make worktree NAME=x   isolated checkout for a concurrent session\n'
	@printf 'make worktree-list     show active worktrees\n'
	@printf 'make worktree-rm NAME=x  remove one\n'

check:
	@fail=0; for t in $(OFFLINE); do \
	  printf '\n=== %s\n' "$$t"; \
	  $(PY) "$$t" || fail=1; \
	done; \
	printf '\n'; \
	if [ $$fail -ne 0 ]; then printf 'CHECK FAILED\n'; exit 1; fi; \
	printf 'CHECK GREEN\n'

check-live: check
	@printf '\nLIVE tests drive Resolve — it must be open with no modal dialog.\n'
	@fail=0; for t in $(LIVE); do \
	  printf '\n=== %s\n' "$$t"; \
	  $(PY) "$$t" || fail=1; \
	done; \
	printf '\n'; \
	if [ $$fail -ne 0 ]; then printf 'LIVE CHECK FAILED\n'; exit 1; fi; \
	printf 'LIVE CHECK GREEN\n'

hooks:
	@git config core.hooksPath .githooks
	@printf 'pre-commit gate installed (core.hooksPath=.githooks)\n'

# Concurrent sessions. Two agents in one checkout is how STATUS.md ended up
# saying pipeline G2 was both done and to-do. One session per worktree.
# AGENTS.md §Concurrent sessions.
worktree:
	@test -n "$(NAME)" || { printf 'usage: make worktree NAME=music\n'; exit 1; }
	@git worktree add "../media-studio-$(NAME)" -b "lane/$(NAME)"
	@printf '\nopen the second session in ../media-studio-%s\n' "$(NAME)"
	@printf 'then run: make hooks   (the gate is per-checkout)\n'

worktree-list:
	@git worktree list

worktree-rm:
	@test -n "$(NAME)" || { printf 'usage: make worktree-rm NAME=music\n'; exit 1; }
	@git worktree remove "../media-studio-$(NAME)"
	@printf 'removed. branch lane/%s still exists — delete it if merged.\n' "$(NAME)"
