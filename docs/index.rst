.. pyworkforce documentation master file, created by
   sphinx-quickstart on Fri May 13 15:38:45 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyworkforce
===========
Tools for workforce management problems such as queue staffing, shift scheduling,
rostering, and operations research optimization.

#########################################################################

pyworkforce helps answer practical planning questions:

* How many resources are needed to handle incoming demand?
* How many people should be assigned to each predefined shift?
* Which named resources should work each day and shift?

The package exposes focused solvers for queuing, scheduling, and rostering
workflows, with examples and API references for each module.

Installation:
#############

We recommend installing pyworkforce in a virtual environment::

   pip install pyworkforce

pyworkforce supports Python 3.12, 3.13, and 3.14.

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
