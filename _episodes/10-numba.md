---
title: "Numba for automatic optimisation"
teaching: 50
exercises: 25
questions:
- "How can I get performance close to that of machine-code from my hand-written Python code?"
- "How can I target GPUs from Python?"
keypoints:
- "Use the `@jit` decorator to just-in-time compile Python functions with Numba"
- "Pay attention to the kinds of object and operation you use in your functions to allow Numba to optimise them"
---

We know that due to various design decisions in Python, programs written
using pure Python operations are slow compared to equivalent code written
in a compiled language. We have seen that Numpy provides a lot of
operations written in compiled languages that we can use to escape from
the performance overhead of pure Python. However, sometimes we do still
need to write our own routines from scratch. This is where Numba comes in.
Numba provides a *just-in-time compiler*. If you have used languages like
Java, you may be familiar with this. While Python can't easily be compiled
in the way languages like C and Fortran are, due to its flexible type
system, what we can do is compile a function for a given data type once
we know what type it can be given. Subsequent calls to the same function
with the same type make use of the already-compiled machine code that was
generated the first time. This adds a significant overhead to the first
run of a function, since the compilation takes longer than the less
optimised compilation that Python does when it runs a function; however,
subsequent calls to that function are generally significantly faster.
If another type is supplied later, then it can be compiled a second time.

Numba makes extensive use of a piece of Python syntax known as
"decorators". Decorators are labels or tags placed before function
definitions and prefixed with `@`; they modify function definitions,
giving them some extra behaviour or properties.

## First example of Numba

(Adapted from the
[5-minute introduction to Numba](https://numba.pydata.org/numba-doc/latest/user/5minguide.html).)

~~~
from numba import jit
import numpy as np

@jit(nopython=True)
def a_plus_tr_tanh_a(a):
    trace = 0
    for i in range(a.shape[0]):
        trace += np.tanh(a[i, i])
    return a + trace
~~~
{: .language-python}

Some things to note about this function:

* The decorator `@jit(nopython=True)` tells Numba to compile this code
  in "no Python" mode (i.e. if it can't work out how to compile this
  function entirely to machine code, it should give an error rather than
  partially using Python)
* The function accepts a Numpy array; Numba performs better with Numpy
  arrays than with e.g. Pandas dataframes or objects from  other libraries.
* The array is operated on with Numpy functions (`np.tanh`) and broadcast
  operations (`+`), rather than arbitrary library functions that Numba
  doesn't know about.

To time this, it's important to run the function once during the
setup step, so that it gets compiled before we start trying to time
its run time. Save the script as `first_numba.py` and try the
following:

~~~
$ python -m timeit --setup='import numpy as np; \
    from first_numba import a_plus_tr_tanh_a; \
    a = np.arange(10000).reshape((100, 100)); \
    a_plus_tr_tanh_a(a)' \
    'a_plus_tr_tanh_a(a)'
~~~
{: .language-bash}

~~~
100000 loops, best of 5: 3.2 usec per loop
~~~
{: .output}

How does this compare with the naive version? Commenting out the
`@jit` decorator in `first_numba.py` an re-running the same timing
command:

~~~
2000 loops, best of 5: 133 usec per loop
~~~
{: .output}

This is a 42x speedup. Not quite as fast as we got in some of our
Numpy optimisations, but in the same ballpark.

It might be possible to rearrange this function so that it uses
pure Numpy operations throughout rather than a regular Python loop,
but in many cases it either isn't possible or significantly reduces
the readability of the code. In these cases, Numba can provide an
alternative route to a comparable level of performance, with a
lot less work, and more readable code at the end of it.


## Getting parallel

The `@jit` decorator accepts a relatively wide range of parameters.
One is `parallel`, which tells Numba to try and optimise the function
to run with multiple threads. Like previously, we need to control this
threads count at run-time; this time using the `NUMBA_NUM_THREADS`
environment variable.

Editing `first_numba.py` to add the `parallel=True` option to the
`@jit` decorator and re-running with two threads:

~~~
$ NUMBA_NUM_THREADS=2 python -m timeit --setup='import numpy as np; \
    from first_numba import a_plus_tr_tanh_a; \
    a = np.arange(10000).reshape((100, 100)); \
    a_plus_tr_tanh_a(a)' \
    'a_plus_tr_tanh_a(a)'
~~~
{: .language-bash}

~~~
20000 loops, best of 5: 16.5 usec per loop
~~~
{: .output}

Parallelism has successfully multiplied our run time by 4. This is
because when running in parallel, Numba (in fact, the OpenMP runtime)
needs to spin up a team of threads to run the code, and then keep
them synchronised. This takes a finite amount of time, so on very
small functions like the one we've run here it takes longer than the
time saved by running in parallel.

Re-running this with a larger matrix size:

~~~
$ for NUM in 1 2 3 4 6 8 10
> do
> NUMBA_NUM_THREADS=${NUM} python -m timeit --setup='import numpy as np; \
    from first_numba import a_plus_tr_tanh_a; \
    a = np.arange(1000000).reshape((1000, 1000)); \
    a_plus_tr_tanh_a(a)' \
    'a_plus_tr_tanh_a(a)'
> done
~~~
{: .language-bash}

~~~
500 loops, best of 5: 644 usec per loop
500 loops, best of 5: 596 usec per loop
500 loops, best of 5: 266 usec per loop
1000 loops, best of 5: 323 usec per loop
1000 loops, best of 5: 218 usec per loop
2000 loops, best of 5: 160 usec per loop
2000 loops, best of 5: 151 usec per loop
~~~
{: .output}

It's important to check the case with no parallelisation, and then
multiple different parallelisations, to see whether parallelisation has
given any performance boost at all, and an idea of where the optimal
performance is found.

In this case, 10 threads gives the best time per call to the function, but
in terms of CPU cost it is quite expensive. 151 microseconds times 10
CPU cores is 1510 core-microseconds per call, compared to 644 for the
serial version. The 3-core version however, at 798 core-microseconds, is
only a little less efficient than the serial version, and is still
almost three times faster (compared to the 10-core version's slightly
better than four times).

