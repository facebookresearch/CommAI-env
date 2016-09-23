Meta-documentation
==================

To regenerate a local copy of these documents, do, depending on whether you
want html or pdf docs::

  cd src/docs
  make html

or::

  cd src/docs
  make latexpdf

This documentation can be made publicly available at the URL
https://facebookresearch.github.io/CommAI-env/ simply by checking out
the GitHub repo and running the following command at the root of the project::

    make gh-pages
