---
title: "Dask for parallel data operations"
teaching: 50
exercises: 25
questions:
- "How can I parallelise common library operations across multiple cores and nodes?"
keypoints:
- "Dask will parallelise across as many resources as it is asked to"
- "Dask also has drop-in replacements for many other common
operations, e.g. in scikit-learn"
---

While the strategies we've discussed so far can improve the
performance of your software on a single node, there will always be
cases where you require more resources than a single node can
provide. For example, a single iteration of your algorithm may take
longer than the wall-time limits of the machine, or your algorithm may
be sequential, so that you can't split it and run each step
separately. You may also find that for very large problems, the memory
capacity of the node becomes a limiting factor; in this case, using
more than one node is not only necessary for to achieve a speedup, but
to even run the problem at all.

Once we expand our programs beyond running on a single node, then we
have more concerns to consider. The main one of these is communication
between the nodes: each node needs to be aware of what it needs to do,
and to be kept updated on any information from the other nodes
necessary to keep doing this. A confounding factor is that
communication between nodes is in most cases significantly slower than
communicating between processes or threads running on the same node,
so many algorithms will pay a significant performance penalty for
running across multiple nodes.

Two commonly-encountered models of parallelism are:

* The co-ordinator&ndash;worker pattern, where one process or node
  (the co-ordinator) has a privileged state and allocates work for
  other processes (the workers). This has the advantages that it is
  relatively conceptually simple to adapt an existing program
  to&mdash;find the expensive bits of computation that do not have
  data dependencies, and farm those out to workers. In many cases this
  can also make load balancing easier&mdash;if one process has a
  panoptic view of what every process is doing, it can make sure that
  each has a roughly similar amount of work to do, avoiding the
  situation where some workers finish their work much earlier and
  waste their time idling rather than picking up work from other
  processes still working. A disadvantage is that it doesn't scale
  well to large numbers of processes&mdash;once you have thousands of
  processes running, then the co-ordinator may not be able to keep up
  with giving them work, typically because there is not enough
  bandwidth to send the data each process needs and receive the
  result.
* A more "distributed", "collectivist" or "flat" approach, where all
  processes and nodes have the same status, and know which other
  processes need to be sent data and be received from. Libraries for
  this approach provide collective operations for aspects that require
  global communications, such as global sums. The advantage here is
  that the full bandwidth of the network can be used, rather than
  relying on the links to and from a co-ordinator process. The
  trade-off is that it can be more conceptually difficult to
  understand how to adapt a program to this approach, and how to
  understand what an existing program taking this approach is doing.
  

## Introducing Dask

Dask is a library that takes functionality from a number of popular
libraries used for scientific computing in Python, including Numpy,
Pandas, and scikit-learn, and extends them to run in parallel across a
variety of different parallelisation setups. This includes multiple
threads or multiple processes on the same node, as well as using
multiple nodes.

For today, we're going to jump straight to the most advanced case and
look at how we can use it to run across multiple nodes on an HPC
cluster.

While multi-node support is built in to Dask, we will use the
`dask-mpi` package to help Dask interact with Slurm to create the
right number of processes. Since we need to install extra packages, we
first need to load the environment that we created earlier today.

~~~
$ module load anaconda/2019.03
$ source activate scw_test
~~~
{: .language-bash}

Now, since we are going to use the MPI libraries that are installed on
Sunbird, we can't use Conda to install `dask-mpi`, since this will
instead use Anaconda's own version of MPI, which doesn't work
properly. Instead, we need to load the MPI libraries, and then install
`dask-mpi` with `pip`.

~~~
$ module load compiler/intel/2019/5 mpi/intel/2019/5
$ pip install mpi4py dask-mpi dask-ml
~~~
{: .language-bash}


## The Message Passing Interface

While there isn't time to talk in detail about MPI (the Message
Passing Interface) today, it's worth talking a little about how it
works so that we can better understand how Dask interacts with it.

With MPI, multiple copies of the same program (_ranks_ in the MPI
jargon) are run, and these communicate with each other to share
work. These are usually run with a utility called `mpirun` (or
sometimes `mpiexec`), which starts many copies of a given program on
the specified nodes.

On a cluster, `mpirun` is integrated with the scheduler
(e.g. Slurm), so knows which nodes to place processes on
automatically. Many clusters provide their own wrappers for `mpirun`
to make this integration work better; in Slurm, this utility is
`srun`. (You may remember we used `srun` with GNU Parallel to place
processes on appropriate nodes; this was a special case where we only
wanted a single process at a time.)

More than one process can run per node&mdash;sometimes
it makes sense to run as many processes as there are CPU cores, since
then you don't also need to think about other sorts of parallelism.
Programs that are aware of MPI will then talk to the MPI library
(which `mpirun` makes available to them) to get enough information
about the number and placement of processes to be able to do their
work.

While MPI by default uses a collectivist approach to its
communications, Dask's model is a co-ordinator&ndash;worker one. To
translate between these, `dask-mpi` finds the number of ranks from
MPI, and does the following with them:

* the first rank becomes the co-ordinator for the team of workers,
* the second rank continues executing the program in serial, and
* any remaining ranks become workers, and do any work that is
  submitted to them from the second rank.
  
It then ignores MPI completely, using Dask's built-in communications
methods to communicate between the processes instead. MPI is only used
to create the right number of processes, and communicate that number
to Dask.
  
If we are programming in parallel effectively, most of our computation
time will be spent having the workers do the work. If each piece of
work is quite expensive, then this may mean that both the co-ordinator
and the serial part of the work sit idling. Since in general we want
each process to use a full node, then these processes can end up
wasting two full nodes of computational resource that could have been
getting us our results faster. Anticipating this, we can start two
more processes than we have nodes, so that the workers can do some
work on the same nodes as the co-ordinator and serial process sit.

So, to get Dask working with MPI under Slurm, we need two things:

* a Python program that uses `dask-mpi` to get information from MPI
  about the setup it is running under, and
* a job script that uses `srun` to launch the right number of these
  programs

Let's look at these in turn. Firstly, the job script to submit this
workload to the cluster looks like this:

~~~
#!/bin/bash --login
###
# Output file location
#SBATCH --output dasktest.out.%J
# Dask outputs a lot of debug information to stderr
# so let's direct that to a separate file
#SBATCH --error=dasktest.err.%J
# For now, let's use two nodes, with one 
#SBATCH --nodes=2
#SBATCH --ntasks=2
# We want to use the full node
#SBATCH --cpus-per-task=40
#SBATCH --exclusive
# Time limit for this job
#SBATCH --time 00:10:00
# specify our current project
# change this for your own work
#SBATCH --account=scw1389
# specify the reservation we have for the training workshop
# remove this for your own work
# replace XX with the code provided by your instructor
#SBATCH --reservation=scw1389_XX
###

# Get MPI and Anaconda ready to use
module load anaconda/2019.03 compiler/intel/2019/5 mpi/intel/2019/5
source activate scw_test

# Get Slurm to run the Python program that uses Dask
srun --overcommit \
     --distribution=cyclic \
	 --nodes=${SLURM_NNODES} \
	 --ntasks=$[SLURM_NTASKS+2] \
	 --cpus-per-task=${SLURM_CPUS_PER_TASK} \
	 python dasktest.py
~~~
{: .bash}

While the `#SBATCH` directives are explained inline, in the call to
`srun`, the meaning of the flags is:

* `--overcommit`: run multiple MPI ranks on a single core/slot
* `--distribution=cyclic`: instead of placing 0 and 1 on the same node,
  then 2 and 3, place 0 and N-2 on the first node, 1 and N-1 on the
  second, so that workers overlap with the co-ordinator and serial
  process
* `--nodes=${SLURM_NNODES}` and
  `--cpus-per-task=${SLURM_CPUS_PER_TASK}` - get these variables from
  Slurm
* `--ntasks=$[SLURM_NTASKS+2]` - get the number of tasks in Slurm,
  then add the 2 extra


Next, the program itself. This is a Dask version of [a Scikit-learn
example][scikit-learn example] making use of the `GridSearchCV` function.

~~~
from os import environ
from datetime import datetime

from dask_mpi import initialize
from distributed import Client

from sklearn import datasets
from sklearn.model_selection import train_test_split

# Get the Dask version of GridSearchCV
from dask_ml.model_selection import GridSearchCV

from sklearn.metrics import classification_report
from sklearn.svm import SVC


def run_test(client):
    print(__doc__)

    # Loading the Digits dataset
    digits = datasets.load_digits()

    # To apply an classifier on this data, we need to flatten the image, to
    # turn the data in a (samples, feature) matrix:
    n_samples = len(digits.images)
    X = digits.images.reshape((n_samples, -1))
    y = digits.target

    # Split the dataset in two equal parts
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.5, random_state=0)

    # Set the parameters by cross-validation
    tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-3, 1e-4],
                         'C': [1, 10, 100, 1000]},
                        {'kernel': ['linear'], 'C': [1, 10, 100, 1000]}]

    scores = ['precision', 'recall']

    for score in scores:
        print("# Tuning hyper-parameters for %s" % score)
        print()

        # scheduler=client makes sure that Dask uses the correct communications
        clf = GridSearchCV(
            SVC(), tuned_parameters, scoring='%s_macro' % score,
            scheduler=client
        )
        clf.fit(X_train, y_train)

        print("Best parameters set found on development set:")
        print()
        print(clf.best_params_)
        print()
        print("Grid scores on development set:")
        print()
        means = clf.cv_results_['mean_test_score']
        stds = clf.cv_results_['std_test_score']
        for mean, std, params in zip(means, stds, clf.cv_results_['params']):
            print("%0.3f (+/-%0.03f) for %r"
                  % (mean, std * 2, params))
        print()

        print("Detailed classification report:")
        print()
        print("The model is trained on the full development set.")
        print("The scores are computed on the full evaluation set.")
        print()
        y_true, y_pred = y_test, clf.predict(X_test)
        print(classification_report(y_true, y_pred))
        print()

    # Note the problem is too easy: the hyperparameter plateau is too flat and
    # the output model is the same for precision and recall with ties in
    # quality.


def main():
    # Work out from the environment how many threads to allocate
    num_threads = int(environ.get(
        'SLURM_CPUS_PER_TASK',
        environ.get('OMP_NUM_THREADS', 1)
    ))

    # Create the Dask workers
    initialize(interface='ib0', nthreads=num_threads)

    # Create the Dask object that will manage the communications
    client = Client()

    start = datetime.now()
    run_test(client=client)
    end = datetime.now()

    print("Time taken: {end - start}")


if __name__ == '__main__':
    main()
~~~
{: .language-python}



[scikit-learn example]: https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_digits.html#sphx-glr-auto-examples-model-selection-plot-grid-search-digits-py
