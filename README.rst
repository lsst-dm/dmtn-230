.. image:: https://img.shields.io/badge/dmtn--230-lsst.io-brightgreen.svg
   :target: https://dmtn-230.lsst.io/
.. image:: https://github.com/lsst-dm/dmtn-230/workflows/CI/badge.svg
   :target: https://github.com/lsst-dm/dmtn-230/actions/

########################################
RSP HiPS service implementation strategy
########################################

DMTN-230
========

HiPS is an IVOA-standard protocol for providing a hierarchical, pre-rendered view of sky survey data.
It is one of the ways in which Rubin Observatory will make available its survey data to data rights holders.
This tech note describes the implementation strategy for the Rubin Science Platform HiPS service.


**Links:**

- Publication URL: https://dmtn-230.lsst.io/
- Alternative editions: https://dmtn-230.lsst.io/v
- GitHub repository: https://github.com/lsst-dm/dmtn-230
- Build system: https://github.com/lsst-dm/dmtn-230/actions/

Build this technical note
=========================

You can clone this repository and build the technote locally if your system has Python 3.11 or later:

.. code-block:: bash

   git clone https://github.com/lsst-dm/dmtn-230
   cd dmtn-230
   make init
   make html

Repeat the ``make html`` command to rebuild the technote after making changes.
If you need to delete any intermediate files for a clean build, run ``make clean``.

The built technote is located at ``_build/html/index.html``.

Publishing changes to the web
=============================

This technote is published to https://dmtn-230.lsst.io/ whenever you push changes to the ``main`` branch on GitHub.
When you push changes to a another branch, a preview of the technote is published to https://dmtn-230.lsst.io/v.

Editing this technical note
===========================

The main content of this technote is in ``index.rst`` (a reStructuredText file).
Metadata and configuration is in the ``technote.toml`` file.
For guidance on creating content and information about specifying metadata and configuration, see the Documenteer documentation: https://documenteer.lsst.io/technotes.
