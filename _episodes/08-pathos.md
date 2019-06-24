---
title: "Multiprocessing with Pathos"
teaching: 40
exercises: 20
questions:
- "How can I distribute subtasks across multiple cores or nodes?"
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
a similar process process to the one  we used for accepting command-line
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
    filenames = [f'b{beta}_m{m}.dat'
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

This will run the Monte Carlo simulation for the seven parameter sets
$(\beta=0.5, m=0.5)$, $(\beta=0.5, m=1.0)$, $(\beta=1.0, m=0.5)$,
$(\beta=1.0, m=1.0)$, $(\beta=1.0, m=2.0)$, $(\beta=2.0, m=1.0)$,
$(\beta=2.0, m=2.0)$. Each uses the same values of `h` and
`iteration_count`, and the filename in each case is decided
programmatically.

