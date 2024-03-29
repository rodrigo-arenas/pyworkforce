.. pyworkforce documentation master file, created by
   sphinx-quickstart on Fri May 13 15:38:45 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyworkforce
===========
Standard tools for workforce management, queuing, scheduling, rostering and optimization problems.

#########################################################################

This package implements a python interface for common problems in operations research
applied to queue and scheduling problems, among others.

Installation:
#############

It's advised to install pyworkforce using a virtual env, inside the env use::

   pip install pyworkforce

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: User Guide / Tutorials:

   tutorials/erlangc
   tutorials/erlangc_example
   tutorials/scheduling
   tutorials/rostering

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/erlangc
   api/multierlangc
   api/min_abs_difference
   api/min_required_resources
   api/min_hours_roster

.. toctree::
   :maxdepth: 2
   :caption: Release Notes

   release_notes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
