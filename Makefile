NAME=crossref-source
PLUGIN_NAME="CrossRef"

ZIP=$(NAME).zip

SRC=crossref-source

SRC_FILES=__init__.py crossref_source.py

SRC_FILES_ABS=$(addprefix ${SRC}/,${SRC_FILES})


$(ZIP): $(SRC_FILES_ABS)
	cd ${SRC}; zip -r ../$(ZIP) ${SRC_FILES}

.PHONY: clean zip install test

clean:
	rm -f ${ZIP}

zip: $(ZIP)

install: $(ZIP)
	calibre-customize --a $(ZIP)

uninstall:
	calibre-customize --r $(PLUGIN_NAME)

test: install
	calibre-debug -e $(SRC)/test.py
