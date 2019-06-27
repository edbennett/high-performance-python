---
title: "Multiprocessing with Pathos"
teaching: 30
exercises: 30
questions:
- "How can I distribute subtasks across multiple cores or nodes?"
objectives:
- "Be able to distribute work to multiple cores using parallel pools"
- "Know where to look to extend this to multiple nodes"
- "Understand how to break up more monolithic tasks into subtasks that can be parallelised"
keypoints:
- "The `ParallelPool` in Pathos can spread work to multiple cores."
- "Look closely at loops and other large operations in your program to identify where there is no data dependency, and so parallelism can be added"
- "Pyina has functions that extend the parallel map to multiple nodes"
---

So far, we have distributed processes to multiple cores and nodes
using GNU Parallel, but this has required spinning up separate
instances of Python and importing the same libraries repeatedly.
If the task that we are performing is brief, then this is a large
overhead, wasting time that could be spent doing our computation.
We've also seen that Numpy can distribute some tasks to multiple
cores, but isn't always particularly good at it.

Fortunately, Python includes tools for more explicitly distributing
tasks across more than one CPU. Pathos is a tool that extends this
to work across multiple nodes, and provides other convenience
improvements over Python's built-in tools.

To start with, we need to install Pathos. 
Pathos isn't installed as part of the standard Anaconda distribution;
it can be installed from the `conda-forge` channel though.

~~~
$ conda install pathos
~~~
{: .language-bash}

## A toy example

To get a feel for how Pathos can help run functions in parallel,
let's consider the toy example of raising numbers to powers.

We can run this in an interactive interpreter, via `python` or
`ipython`:

~~~
>>> from pathos.pools import ParallelPool
>>> pool = ParallelPool(nodes=10)
>>> pool.map(pow, [1, 2, 3, 4], [5, 4, 3, 2])
[1, 16, 27, 16]
~~~
{: .language-python}

The key function here is `ParallelPool.map()`, which takes the function
provided as the first argument, and calls it repeatedly using the
arguments supplied in the subsequent lists. If you have used `map` in
Python, this function is an extension; rather than only taking one list
of arguments, it takes multiple: one per parameter that the function
accepts.

In this case, `pow()` has two parameters: the base and the exponent.
Each pair of values is passed to `pow` in turn. The ParallelPool
holds a certain number of Python processes running on different
cores, and decides which one is available to run a given set of
parameters. If all processes are busy, then it will wait until one
is free, and then send the parameters over.

Of course, most of the time the function we want to run in parallel
isn't a single mathematical function, but a longer-running function
that we have written ourselves.


## Getting ready to multiprocess

Before we can ask Pathos to run our code in parallel, we need to
structure it in a way that Pathos can do this easily. This is
a similar process to the one  we used for accepting command-line
arguments; the difference is that now instead of using the `argparse`
module and declaring the arguments that way, we declare a function
that accepts the arguments in question. (It's good practice to do this
whenever you're writing a program anyway, and we could have done this
as an extra step when tweaking things for GNU Parallel.)

The example `mc.py` that we looked at earlier is already in this shape.
Rather than breaking the existing program to test Pathos, we can write
a second program that loads `mc.py` as a library.

~~~
from pathos.pools import ParallelPool
from mc import run_mc

def run_in_parallel(betas, ms, h, iteration_count):
    # Check that lists are all the same length
    assert len(betas) == len(ms)

    # Generate lists of the same value of h and iteration_count
    hs = [h] * len(betas)
    iteration_counts = [iteration_count] * len(betas)

    # Generate a list of filenames to output results to
    filenames = [f'mc_data/b{beta}_m{m}.dat'
                 for beta, m in zip(betas, ms)]

    # Create a parallel pool to run the functions
    pool = ParallelPool(nodes=10)

    # Run the work
    pool.map(run_mc, ms, hs, betas, iteration_counts, filenames)

if __name__ == '__main__':
    run_in_parallel(
        [0.5, 0.5, 1.0, 1.0, 1.0, 2.0, 2.0],
        [0.5, 1.0, 0.5, 1.0, 2.0, 1.0, 2.0],
        1.0,
        100000
    )
~~~
{: .language-python}

Save this as `mc_pathos.py`, and run it via:

~~~
$ mkdir mc_data    # Make sure that the directory to hold the output data is created
$ python mc_pathos.py
~~~
{: .language-bash}

This will run the Monte Carlo simulation for the seven parameter sets
$(\beta=0.5, m=0.5)$, $(\beta=0.5, m=1.0)$, $(\beta=1.0, m=0.5)$,
$(\beta=1.0, m=1.0)$, $(\beta=1.0, m=2.0)$, $(\beta=2.0, m=1.0)$,
$(\beta=2.0, m=2.0)$. Each uses the same values of `h` and
`iteration_count`, and the filename in each case is decided
programmatically.


## Parameter scans

We've just used 10 cores to perform 7 independent computations. Even
if the computations all take the same length of time, three cores are
sitting idle, so we are 70% efficient at best. If we have seven jobs
that are long enough that we want to use HPC for them, then we'd be
better off using seven independent SLURM jobs; Pathos isn't useful
there. This kind of workflow comes into its own when you have hundreds
or thousands of different values to scan through. But hardcoding lists
of hundreds or thousands of elements is tedious, especially when there
will be lots of repeated values.

Quite often what we'd really like to do is take a set of possible
values for each variable, and then scan over all possible
combinations. With two variables this allows a heatmap or contour plot
to be produced, and with three a volumetric representation could be
generated.

The first tool in our arsenal is the `product` function from the
`itertools` module. This generates tuples containing all possible
combinations of the lists it is given as an argument. Let's check this
at a Python interpreter:

~~~
$ python
~~~
{: .language-bash}

~~~
>>> from itertools import product
>>> numbers = [1, 2, 3, 4, 5]
>>> letters = ['a', 'b', 'c', 'd', 'e']
>>> list(product(numbers, letters))
~~~
{: .language-python}

~~~
[(1, 'a'), (1, 'b'), (1, 'c'), (1, 'd'), (1, 'e'), (2, 'a'), (2, 'b'),
(2, 'c'), (2, 'd'), (2, 'e'), (3, 'a'), (3, 'b'), (3, 'c'), (3, 'd'),
(3, 'e'), (4, 'a'), (4, 'b'), (4, 'c'), (4, 'd'), (4, 'e'), (5, 'a'),
(5, 'b'), (5, 'c'), (5, 'd'), (5, 'e')]
~~~
{: .output}

We need to use the `list` function here to create a list that we can
read, as by default `product` produces a generator. (Great for looping
through, and good for passing to other functions, but not useful for
seeing the results on screen.)

Looking closely, this isn't quite what we want yet. We need all the
first elements to be in one list, and all the second elements to be in
another (and so on). Fortunately, there's another built-in function
that can help us here.

`zip` is a function that is most often used to take a few lists of
many elements, and return one long list, of tuples of few elements.
But if instead we give it many small tuples, we'll get back a short
list of long tuples&mdash;one containing the first elements, one
containng the second elements, and so on.

The only extra ingredient we need to make this work is to be able to
pass in the elements of the result of `product`, rather than the
iterable as a single argument. This is done with the `*`, which when
placed before a list (or other iterable) means "expand this iterable
into multiple arguments". Putting these together:

~~~
>>> list(zip(*product(numbers, letters)))
~~~
{: .language-python}

~~~
[(1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
5, 5), ('a', 'b', 'c', 'd', 'e', 'a', 'b', 'c', 'd', 'e', 'a', 'b',
'c', 'd', 'e', 'a', 'b', 'c', 'd', 'e', 'a', 'b', 'c', 'd', 'e')]
~~~
{: .output}

We now have two tuples of the form that we want to pass in to
`map`. All that remains is to extract them from the list that they're
in. Just like before, this is done with `*`.

Adapting the previous example to scan $\beta$, $m$, and $h$:

~~~
from pathos.pools import ParallelPool
from itertools import product
from mc import run_mc

def run_in_parallel(betas, ms, hs, iteration_count):
    # Check that lists are all the same length
    assert len(betas) == len(ms)
    assert len(betas) == len(hs)

    # Generate a list of the same value of iteration_count
    iteration_counts = [iteration_count] * len(betas)

    # Generate a list of filenames to output results to
    filenames = [f'mc_data/b{beta}_m{m}_h{h}.dat'
                 for beta, m, h in zip(betas, ms, hs)]

    # Create a parallel pool to run the functions
    pool = ParallelPool(nodes=10)

    # Run the work
    pool.map(run_mc, ms, hs, betas, iteration_counts, filenames)

if __name__ == '__main__':
    betas = [0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    ms = [0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    hs = [0.25, 0.5, 1.0, 2.5]
    run_in_parallel(
        *zip(*product(betas, ms, hs)),
        10000
    )
~~~
{: .language-python}

Saving this as `mc_pathos_scan.py` and running it will now generate
324 output files in the `mc_data` directory.

> ## Verifying that it is parallel
>
> When Slurm is running a job on a particular node, it will let us SSH
> directly to that note to check its behaviour. We can use this to
> verify that we are running in parallel as we expect.
>
> Open a new terminal, and SSH to Sunbird again. Use `squeue -u $USER`
> to find out what node your job is running on&mdash;this is the
> right-most column. Then SSH into that node, using `ssh scsXXXX`,
> where `XXXX` is replaced with the node number you got from `squeue`.
>
> Once running on the node, you can use the `top` command to get a
> list of the processes using the most CPU resource, updating every
> second. If your program is parallelising properly, you should see
> multiple `python` processes, all consuming somewhere near 100%
> CPU. (The percentages refer to a single CPU core rather than to the
> available CPU in the machine as a whole.)
>
> If your job (or interactive allocation) ends while you're SSHed into
> the node, then the SSH session will be killed by the system
> automatically.
{: .callout}

> ## Processing file lists
>
> Not all the workloads of this kind will be parameter scans; some
> might be processing large numbers of files instead. Revisit the
> Fourier example from the section on GNU Parallel, and try converting
> it to work with Pathos instead.
>
> You might want to do this in the following steps:
>
> 1. Convert the program to be a function, separating out the
>    behaviour that relates to `argparse` from the behaviour that is
>    the desired computational behaviour.
> 2. Create a second file, as we have done here, to call this new
>    function using Pathos. For now, hardcode a list of images to
>    process.
> 3. Now, adjust the program to read the image list from a file, but
>    hardcode the filename.
> 4. Finally, adjust the program to read the image list filename from
>    the commandline, e.g. using `argparse`.
{: .challenge}

> ## Parameters to scan on the command line
>
> In general, we don't want to hard-code our parameters, even if there
> are only a few and we are using `itertools.product` to generate the
> longer lists.
>
> Adapt the Monte Carlo example above so that it can read the `betas`,
> `ms`, and `hs` lists from the command-line. (The `action="append"`
> keyword argument to `add_argument` will be useful here; the
> `argparse` documentation will tell you more.)
{: .challenge}


<!--- REMOVING THIS SECTION UNTIL IT IS MORE PERFORMANT

## Chunking

Sometimes, we have a large problem that is taking too long, and we
want to parallelise it so that it will finish faster. Unlike the above
cases, it's not immediately obvious how one could split it into subtasks
that can be run independently.

Take for example the multi-dimensional array-broadcasting example that
we followed through in the Numpy episode. This is just performing a
single operation on a large array&mdash;surely that doesn't decompose
into many small tasks?


--->


> ## Surprisingly parallelisable tasks
>
> Sometimes you need to think more carefully about how a task can be
> parallelised. For example, looking back to the example of
> calculating $\pi$ from the previous section, on the surface we are
> only performing a single computation, that returns a single
> number. However, in fact each Monte Carlo sample is independent, so
> could be generated on a separate processor.
>
> Try adapting one of the solutions to the $\pi$ example in the Numpy
> episode to run multiple streams in parallel. Each stream will want
> to report back the count of points inside the circle; totalising and
> calculating the value of $\pi$ then needs to happen in serial.
{: .challenge}


## Multiple nodes

While it is possible to start processes on more than one node using
the Pathos library directly, this is easier to do using Pyina, which
is another part of the Pathos framework.

Since Pyina depends on MPI, it's not available via Conda (as the MPI
installation will change from machine to machine). To install Pyina,
we first need to choose an MPI library, and then install via Pip. On
Sunbird, the first step can be done by loading the appropriate module.

~~~
$ # Get the latest version of the Intel MPI library
$ module load mpi/intel/2019/4
$ # Now install Pyina using this MPI library
$ pip install pyina
~~~
{: .language-bash}

It can be used very similarly to the Pathos library, by creating a
process pool and then using a map function across that pool. The
difference is that Pyina will interact with Slurm to correctly
position tasks on each node.

A toy example:

~~~
from pyina.ez_map import ez_map

# an example function
def host(id):
    import socket
    return "Rank: %d -- %s" % (id, socket.gethostname())

# launch the parallel map of the target function
results = ez_map(host, range(100), nodes = 10)
for result in results:
    print(result)
~~~
{: .language-python}

Pyina makes use of the Message Passing Interface (MPI) to communicate
between nodes and launch instances of Python; "rank" in this context
is an MPI term referring to the index of the process, which is used
for bookkeeping. A full study of what MPI can do (in Python or
otherwise) is beyond the scope of this lesson!

