---
title: "Getting started with Python on Supercomputing Wales"
teaching: 30
exercises: 10
questions:
- "How do I run Python on Supercomputing Wales?"
- "How do I install packages and other Python software on
Supercomputing Wales?"
keypoints:
- "Use `module load anaconda/2021.05` and `source activate` to get started with Anaconda on Sunbird"
- "Create new conda environments with `conda create` when the `base` Anaconda set of packages doesn't meet your needs"
---

Python is one of the most popular programming languages currently
available, and is enjoying a surge in usage in academic research.
Unfortunately, many of the features that allow Python to be learned
and applied so quickly and easily have a computational cost associated
with them, and so when used for heavy computation, Python can easily
be orders of magnitude slower than "traditional" academic languages
like C or Fortran. However, features both within the core Python
language and in extensions to it mean that it doesn't have to be
as slow as the worst case scenario, and Python's reputation as a
"slow" language is perhaps somewhat unfair&mdash;like any language,
when programmed without paying attention to performance, it will
not be performant, but when correctly tuned, it can compete with
C or Fortran.

## Scope of this training

In this workshop we will focus on problems that could benefit from
running on High-Performance Computing (HPC) facilities. Specifically,
this is problems that have some strong element of computation or
simulation, that require large amounts of computing time (hours or
days) to complete, either for a single execution or for a large
batch of related runs (for example, scanning a parameter space, or
processing many different input files).

Cases that we will explicitly not consider today include:

* Real-time control programs or similar where latency of response
  to an external control signal is the performance measure (e.g.
  experimental monitoring programs, high-frequency trading software)
* Programs where the performance bottleneck is interaction with
  the Internet (e.g. Web scrapers)
* Cases where the Python software is not the bottleneck, such as
  programs where Python is used as a scripting language to launch
  other programs not written in Python.


## Managing packages

One of Python's biggest strengths is the breadth of third-party
packages available to extend its functionality. Because of this, in
some ways Python has become a victim of its own success. When running
Python on a supercomputing facility, it isn't sufficient for the
machine to have Python installed and available, you might also need
Numpy, Pandas, and Pillow, all at specific minimum versions, for your
software to work. Now, the system administration team can't create a
bespoke Python environment specifically for your project&mdash;if they
did this for every project using Python, they would have little time
to do anything else.

Pip will let you install packages within your home directory, but
only in a single location. This means that if you have two different
applications that you need to run but that rely on different versions
of particular packages, then you have to uninstall and reinstall
packages each time you switch applications. Worse, if you want to
upgrade to a new version of Python when it is made available on the
system, then you more often than not will need to purge your packages
and reinstall them against the new Python version.

Because of this, virtual environments have become increasingly
popular in the Python community for managing packages. Rather than
having a single installation directory, each project has its own
directory of installed packages, and in some cases, version of Python.

On Supercomputing Wales, the Anaconda Python distribution is
available. This provides the Conda package manager, which can be used
to create virtual environments in which to install your packages.

To start using Conda on Supercomputing Wales, you need to connect
to the Sunbird cluster. To do this, we use SSH, as in the
[Supercomputing Wales training](https://edbennett.github.io/SCW-tutorial/02-logging-in/).

~~~
$ ssh s.a.username@sunbird.swansea.ac.uk
~~~
{: .language-bash}

You will probably then need to type in your cluster password. If you
have forgotten this, you can reset it at
[My Supercomputing Wales](https://my.supercomputing.wales).

Once logged in, you need two commands to load Anaconda. The first
loads the Anaconda module, and the second activates it so that the
commands provided by Conda are available in your current environment.

~~~
$ module load anaconda/2021.05
$ source activate
~~~
{: .language-bash}

You may notice that your Bash prompt changes to have `(base)` at the
start, indicating that you now have the base Anaconda environment
active. To check this, we can run:

~~~
$ which python
~~~
{: .language-bash}

~~~
/apps/local/languages/anaconda/2021.05/bin/python
~~~
{: .output}

This indicates that when you run `python`, the executable that gets
called is the one in `/apps/local/languages/anaconda/2021.05/bin`,
which is indeed the one provided by the Anaconda module.

This module provides the full Anaconda toolchain, which, depending
on your application, may be enough for your usage. However, once
you do need to install packages not provided within this distribution,
then you'll need to create an environment to hold them. Let's do
that now:

~~~
$ conda create -n scw_test python=3.7
~~~
{: .language-bash}

This tells the `conda` command to `create` a new environment, to
give it the name `scw_test`, and to install Python 3.7 into it.
Conda will take a little time to work out what it needs to install,
and once you confirm by typing `y`, then place it in a new directory
in `~/.conda/envs`.

> ## File quotas
>
> Home directories on Sunbird are subject to a quota of 100GB, and
> 100,000 files. Conda environments can be quite large&mdash;an empty
> one contains around 4,000 files. As a result, if your home
> directory is already quite full, you may encounter an error from
> Conda when the quota runs out.
>
> If this happens, then try working out ways to reduce the file count
> in your home directory; for example, by moving some files to
> `/scratch`. If this isn't possible, then contact support around
> the possibility of raising your file count quota.
>
> You can check how much of your quota is available with the `myquota`
> command. The `limit` of 105,000 indicates that you can temporarily
> exceed the 100,000 quota, but you have one week in which to reduce
> the count back to 100,000 before you can no longer create files.
{: .callout}

Once your environment is created, you can activate it so you can
use it to work in with the command

~~~
$ conda activate scw_test
~~~
{: .language-bash}

The prefix at the start of your prompt will now change from `base`
to `scw_test`, to indicate the environment that you have active.
Similarly, `which python` now returns
`~/.conda/envs/scw_test/bin/python`, indicating that this is now
where Python will run from if you run `python`.

So far we have created a relatively bare environemnt, but we know that
later today we will be using Numpy. So let's now install Numpy into
this environment:

~~~
$ conda install numpy
~~~
{: .language-bash}

Conda automatically works out which extra packages need to be present
for Numpy to work, and then prompts to install them.

You could alternatively have specified `numpy` directly to the
`conda create` command, and it would have been installed when the
environment was created.

If you wanted to create a full Anaconda Python installation to base
your environment on, you can do this with
`conda create -n [name] anaconda`; we don't do this here because
it creates a very large number of files and takes a substantial
time to download and install. In general, it's better to only
install packages that you need, since they are less likely to
conflict with each other.

In addition to the packages provided directly by Conda, there is also
a wider community of packages you can access by adding additional channels
to Conda. The `conda-forge` channel is the largest of these; to use it:

~~~
$ conda config --append channels conda-forge
~~~
{: .language-bash}

`--append` here tells Conda to only use `conda-forge` packages if it
can't find them in its usual channels. If you wanted to exclusively
use `conda-forge` packages, then you could use `--add` instead.
Since we are running on Intel CPUs, we prefer the default channels
where possible, since Intel does a lot of work with Anaconda to
optimise the performance of their libraries, including making use
of the Math Kernel Library (MKL) in Numpy.

Now we are able to install some dependencies for the next episode:

~~~
$ conda install fftw pyfftw
~~~
{: .language-bash}

Conda environments can also hold packages from `pip`. For example,
we'll be using the SnakeViz package later today, which is not provided
by Conda. To install this, we can run

~~~
$ pip install snakeviz
~~~
{: .language-bash}

SnakeViz will then install in the Conda environment, without needing
root permissions.

> ## More packages for today
>
> We'll also need the IPython, Matplotlib, Numba, and Pillow packages 
> for some of today's examples.
> For each of these, decide whether to install it via Conda or Pip,
> and install it.
>
> > ## Solution
> >
> > IPython, Matplotlib, Numba, and Pillow are all common packages, and all 
> > are included in the base Anaconda distribution. They can be
> > installed with
> >
> > ~~~
> > $ conda install ipython matplotlib numba pillow
> > ~~~
> > {: .language-bash}
> {: .solution}
{: .challenge}

> ## An environment for your research
>
> So far we have been working in the `scw_test` environment that we
> created to have a place for today's training. For your research, you
> will want to have a separate environment with the libraries that your
> own research software uses installed.
>
> Create a new Conda environment for your research. Give it a useful
> name, and install the version of Python that you plan to use in
> your research. Activate it, and install the packages that your
> research software relies on.
>
> Test that your research software starts running correctly. (Don't
> try to do a full production run now!)
>
> Once you've finished, switch back to the `scw_test` environment.
{: .challenge}


## Start an interactive session to test with

For today, we're going to run a lot of short Python scripts directly
at the terminal. Since it's bad practice to do this on the login node,
but we don't want to write a job script for every test that we want to
try, we will allocate an interactive session on a compute node.
For running real problems, it is much better for you to use a batch
script and submit it to the queue; we can only easily use interactive
sessions today because we have reserved a set of nodes to use.

~~~
$ srun --ntasks=1 --cpus-per-task=10 --account=scw1389 --reservation=scw1389_18 --pty /bin/bash
~~~
{: .language-bash}

Once we are logged into a compute node, we then need to reactivate the
Conda environment that we are working in.

~~~
$ module load anaconda/2021.05
$ source activate scw_test
~~~
{: .language-bash}

Finally, let's get a copy of the code we'll work with in some of the
episodes later today.

~~~
$ cp -r /home/scw1389/high-performance-python/code high-performance-python-examples
$ cd high-performance-python-examples
~~~
{: .language-bash}
