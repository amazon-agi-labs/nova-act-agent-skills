.PHONY: lint lint-frontmatter lint-references lint-tokens lint-crossrefs lint-parity validate check

SKILL_DIR := skills/nova-act

lint:
	python3 -m scripts.lint_skill

lint-frontmatter:
	python3 -m scripts.lint_skill --check frontmatter

lint-references:
	python3 -m scripts.lint_skill --check references

lint-tokens:
	python3 -m scripts.lint_skill --check tokens

lint-crossrefs:
	python3 -m scripts.lint_skill --check crossrefs

lint-parity:
	python3 -m scripts.lint_skill --check parity

validate:
	npx skills-ref validate $(SKILL_DIR)

check: lint validate
