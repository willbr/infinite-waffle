UNAME := $(shell uname)

ifeq ($(UNAME), Darwin)
    PYTHON = python3
else
    ifeq ($(UNAME), Linux)
        PYTHON = python3
    endif
endif

run:
	$(PYTHON) gui.py

watch:
	watchexec -c -r -e .py make run

