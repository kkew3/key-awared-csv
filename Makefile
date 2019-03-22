.PHONY: all install clean

BASEDIR = $(realpath .)
PREFIX ?= ./bin

all: dist/keyedcsv-rename/keyedcsv-rename

dist/keyedcsv-rename/keyedcsv-rename : keyedcsv-rename.py
	pyinstaller -y "$<"

install : $(PREFIX)/keyedcsv-rename

$(PREFIX)/keyedcsv-rename : dist/keyedcsv-rename/keyedcsv-rename
	-mkdir "$(PREFIX)"
	cd "$(PREFIX)"; rm -f keyedcsv-rename; ln -s "$(BASEDIR)/dist/keyedcsv-rename/keyedcsv-rename" keyedcsv-rename

clean:
	rm -f *.spec
