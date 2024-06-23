UNAME := $(shell uname)

ifeq ($(OS),Windows_NT)     # is Windows_NT on XP, 2000, 7, Vista, 10...
	PYTHON := python
else
	ifeq ($(UNAME), Darwin)
		PYTHON := python3
	else
		PYTHON := python
	endif
endif

run:
	$(PYTHON) gui.py

watch:
	watchexec -c -r -e .py make run

