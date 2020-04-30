---
title: "Summary"
teaching: 10
exercises: 0
questions:
- "Which techniques should I use for which types of problem?"
- "What should I do next?"
---

## Breakdown by component

### Vector units

If you are not utilising vector units, consider using **Numpy** data types
rather than built-in ones. If that is impractical, then look into using
**Numba**' to just-in-time compile your application.


### Multiple cores

Does your program naturally divides into many work items that can be processed
simultaneously (for example, a few thousand images, each of which need to be
independently analysed, or different parameter sets that need to be fitted)?
If so, and the work items are large (a minute or longer each), then consider
using ***GNU Parallel*** to run many copies of an existing program on one node.
If the work items are small (a few seconds each), then consider using
***Pathos*** to run many copies of individual Python functions on one node.
If not, then examine where the bottlenecks in your application are, and what
data structures are dominating this. If your application maps nicely to
***Numpy*** data structures and/or ***Scipy*** algorithms, then these will
automatically use multiple cores where possible. Otherwise, You may be able
to use ***Pathos*** to run individual subtasks in parallel, or you may be
able to use ***Dask*** to partition large data structures across multiple
cores.


### GPUs

Check if there are any existing libraries that are related to the problem
you are solving. If so, then try making use of these. Otherwise, look into
using ***Numba*** to compile specific functions to run on the GPU.


### Multiple nodes

Are you already fully using parallelism on a single node? If not, then look
into this first. If yes, then most of the technologies described above for
multiple cores will also work across multiple nodes&mdash;specifically,
***GNU Parallel*** (when used carefully), ***Pathos***, and ***Dask***.


## What next?

This lesson has covered a lot of new topics in a short period of time. It's
tempting to try and apply them all at once. It's tempting to try and jump in
and rearchitect an entire application from scratch to use them all, but that
isn't likely to be the best course of action. Small, targeted changes are
the best place to start, to show that things are working before you have
spent a huge amount of time on them.

Some general thoughts:

* If you don't have your source code in a version control system like Git,
  then it will be difficult to keep track of as you make changes. If you
  don't want to set up Git before starting work, then make sure you take
  regular backups of your code to roll back to.
* If you don't have a set of unit tests to verify that your software is
  working correctly, then it will be hard to verify that the changes you
  make to optimise the performance don't break the software. If you aren't
  able to write a set of unit tests before starting, then establish a set
  of tests that you can run by hand to check that the results you get are
  still correct.
* Check that the tool that you want to optimise runs in consistent time.
  If it doesn't, why not? Is there anything you can do to make it run
  in consistent time in repeated runs? If not, then how will you know if
  your improvements have made it faster, or if it's just random chance?
* Since you are going to need to do timing tests of your software a lot
  during the optimisation process, try to isolate a sufficiently small
  test case that it will run in a minute or two&mdash;long enough that
  the time it takes to start a Python interpreter doesn't dominate, but
  short enough that you spend more time writing code than waiting for it
  to run.
* Profile your software and identify the functions that are taking up the
  largest amount of the run time. These are where it probably makes sense to
  target your efforts.
* Pick the technology from the above that looks most promising for the
  bottleneck that you are facing. Try and implement it in a minimal case,
  and see if it improves performance. If it does, then you can roll it out
  to the rest of the application, checking the performance as you go to
  ensure that it is still speeding things up, and that your tests still
  pass.
* If the performance still isn't good enough for your needs, then repeat
  the last step with another promising technology.
* If you've implemented all the technologies discussed today, then you
  may be up against the limits of what Python can do for you. You may need
  to consider learning a language like C++ or Fortran, and rewriting the
  most computationally-intensive portions of your applications in one of
  these languages so that they are better able to access the full capability
  of the machine. Depending on the complexity of the application, it may
  make sense to rewrite the entire application, or to expose the rewritten
  portions as a library that you can call from your existing Python code
  (Cython and Numpy provide ways of doing this, among other libraries).

A hackathon event is a good opportunity to start on this road, with others
there to share the journey with you.