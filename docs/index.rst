.. pyworkforce documentation master file, created by
   sphinx-quickstart on Fri May 13 15:38:45 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyworkforce
===========
Common tools for workforce management,
schedule and optimization problems built on top of packages like google's
or-tools and custom modules.

#########################################################################
This package implements a python interface for common problems in operations research
applied to queue and scheduling problems, among others.

Installation:
#############

Install pyworkforce

It's advised to install pyworkforce using a virtual env, inside the env use::

   pip install pyworkforce

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: User Guide / Tutorials:

   tutorials/erlangc
   tutorials/erlangc_example
   tutorials/scheduling

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/erlangc
   api/multierlangc
   api/min_abs_difference
   api/min_required_resources

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
