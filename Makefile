DOCS_ROOT=src/docs
GH_PAGES_SOURCES = $(DOCS_ROOT)/source $(DOCS_ROOT)/Makefile src/core src/worlds src/tasks src/view

# automatic deployment of documentation into GitHub based on:
# http://nikhilism.com/post/2012/automatic-github-pages-generation-from/
gh-pages:
	git checkout gh-pages
	rm -rf $(addprefix $(DOCS_ROOT)/, build _sources _static _modules)
	git checkout master $(GH_PAGES_SOURCES)
	git reset HEAD
	make -C $(DOCS_ROOT) html
	mv -fv $(DOCS_ROOT)/build/html/* ./
	rm -rf $(GH_PAGES_SOURCES) $(DOCS_ROOT)/build
	git add -A
	git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`" && git push origin gh-pages ; git checkout master
