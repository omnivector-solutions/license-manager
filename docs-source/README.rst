.. figure:: https://github.com/omnivector-solutions/license-manager/blob/main/docs-source/src/images/logo.png
   :alt: Logo
   :align: center
   :width: 80px

   An Omnivector Solutions initiative

===============================
 License Manager Documentation
===============================

This repository contains the source for the License Manager Official Documentation page.

It is built using [sphinx](https://www.sphinx-doc.org/en/master/) to render the source into
a static website.


Preparing the Docs
==================

Before building or publishing the documentation, please make sure the documentation source is up to
date with the published versions of the ``license-manager-agent`` and ``license-manager-backend``.

Next, create an entry in the ``docs-source/CHANGELOG.rst`` for the documentation updates.

Finally, create a "topic" branch in git for any changes to the documentation source and for the
generated documenation that will be published:

.. code-block:: bash

   git checkout -b <branch-name-for-pull-request>
   git add src/*


Build the Docs
==============

To build the documentation static site, run the following command::

    $ make docs

This will build HTML documentation in the ``docs`` diretory in the root of the license-manager project.


Publishing the Docs
===================

To publish the documentation, you will need to add all the artifacts in the ``docs`` directory via git:

.. code-block:: bash

   git add ../docs/*
   git commit
   git push -u origin <branch-name-for-pull-request>


Once the pull-request has been merged into main, the documentation will automatically be published.


Other Commands
==============

To lint the python files in the ``src`` directory, run::

    $ make lint


To clean up build artifacts, run::

    $ make clean
