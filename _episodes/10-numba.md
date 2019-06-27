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


## Universal functions

(Adapted from the
[Scipy 2017 Numba tutorial](https://github.com/gforsyth/numba_tutorial_scipy2017/blob/master/notebooks/07.Make.your.own.ufuncs.ipynb))

Recall how in Numpy there are functions that act on whole arrays,
element-wise. These are known as "universal functions", or "ufuncs"
for short. Numpy has the facility for you to define your own ufuncs,
but it is quite difficult to use. Numba makes this much easier with
the `@vectorize` decorator. With this, you are able to write a
function that takes individual elements, and have it extend to operate
element-wise across entire arrays.

For example, consider the (relatively arbitrary) trigonometric
function:

~~~
import math

def trig(a, b):
    return math.sin(a ** 2) * math.exp(b)
~~~
{: .language-python}

Let's put this function in a file, `trig.py`.
If we try calling this function on a Numpy array, we correctly get an
error, since the `math` library doesn't know about Numpy arrays, only
single numbers.

However, if we use Numba to "vectorize" this function, then it becomes
a ufunc, and will work on Numpy arrays!

~~~
import numpy as np
from numba import vectorize
from trig import trig

a = np.ones((5, 5))
b = np.ones((5, 5))

vec_trig = vectorize()(trig)

vec_trig(a, b)
~~~
{: .language-python}

How does the performance compare with using the equivalent Numpy
whole-array operation? Adding the following lines to `trig.py`:

~~~
import numpy as np
from numba import vectorize

vec_trig = vectorize()(trig)

def numpy_trig(a, b):
    return np.sin(a ** 2) * np.exp(b)
~~~
{: .language-python}

~~~
$ python -m timeit --setup='import numpy as np; \
    import trig; \
    a = np.random.random((1000, 1000)); \
	b = np.random.random((1000, 1000))' \
	'trig.vec_trig(a, b)'
$ OMP_NUM_THREADS=1 python -m timeit --setup='import numpy as np; \
    a = np.random.random((1000, 1000)); \
	b = np.random.random((1000, 1000))' \
	'trig.numpy_trig(a, b)'
~~~
{: .language-bash}

~~~
Numba: 10 loops, best of 5: 31.2 msec per loop
Numpy: 50 loops, best of 5: 5.17 msec per loop
~~~
{: .output}

So Numba isn't quite competitive with Numpy in this case. But Numba
still has more to give here: notice that we've forced Numpy to only
use a single core. What happens if we use ten cores with Numpy?

~~~
$ OMP_NUM_THREADS=10 python -m timeit --setup='import numpy as np; \
    a = np.random.random((1000, 1000)); \
	b = np.random.random((1000, 1000))' \
	'trig.numpy_trig(a, b)'
~~~
{: .language-bash}

~~~
50 loops, best of 5: 5.56 msec per loop
~~~
{: .output}

Numpy doesn't parallelise this particular operation very well. But
Numba can also parallelise. If we alter our call to `vectorize`, we
can pass the keyword argument `target='parallel'`. However, when we do
this, we also need to tell Numba in advance what kind of variables it
will work on&mdash;unlike with `@jit`, it can't work this out and then
parallelise. So our `vectorize` call becomes:

~~~
vec_trig = vectorize('float64(float64, float64)', target='parallel')(trig)
~~~
{: .language-python}

This tells Numba that the function accepts two variables of type
`float64` (8-byte floats, also known as "double precision"), and
returns a single `float64`. Adding this into `trig.py` and re-running
the timing gives:

~~~
$ NUMBA_NUM_THREADS=10 python -m timeit --setup='import numpy as np; \
    a = np.random.random((1000, 1000)); \
	b = np.random.random((1000, 1000))' \
	'trig.vec_trig(a, b)'
~~~
{: .language-bash}

~~~
50 loops, best of 5: 4.26 msec per loop
~~~
{: .output}

This has used 42.6 core-milliseconds, so is pretty efficient
parallelisation!

> ## How parallel can this go?
>
> The previous example parallelises almost linearly to 10 cores. We
> have 40 cores available in a node, so can Numba use all of these
> efficiently?
>
> We've been running on a 10-core interactive session, so will need to
> submit a job to test 40 cores.
>
> Write a job script to submit the above `timeit` command to run on 40
> cores on a single node. (You can request 1 node in `--exclusive`
> mode to get this.) How does the timing compare with 10 cores?
>
> > ## Solution
> >
> > I see:
> >
> > ~~~
> > 200 loops, best of 5: 1.32 msec per loop
> > ~~~
> > {: .output}
> >
> > Compared to 31.2ms on one core, this is 59% efficient, so not
> > perfect but not bad by any stretch. It's certainly better than
> > Numpy.
> {: .solution}
{: .challenge}

> ## Another ufunc
>
> Try creating a ufunc to calculate the discriminant of a quadratic
> equation, $\Delta = b^2 - 4ac$. (For now, make it a serial
> function.)
>
> Compare the timings with using Numpy whole-array operations in
> serial. Do you see the results you might expect?
>
> > ## Solution
> >
> > ~~~
> > @vectorize
> > def discriminant(a, b, c):
> >     return b**2 - 4 * a * c
> > ~~~
> > {: .language-python}
> >
> > Timing this gives me 3.73 microseconds, whereas the `b ** 2 - 4 *
> > a * c` Numpy expression takes 13.4 microseconds&mdash;almost four
> > times as long. This is because each of the Numpy arithmetic
> > operations needs to create a temporary array to hold the results,
> > whereas the Numba ufunc can create a single final array, and
> > use smaller intermediary values.
> {: .solution}
{: .challenge}

## Programming GPUs

We don't have time to look at this in detail, but an example of how
GPUs can be programmed with Numba:

~~~
from numba import vectorize

@vectorize(['int64(int64, int64)'], target='cuda')
def add_ufunc(x, y):
    return x + y
~~~
{: .language-python}

More information on programming your GPU with Numba can be found at
[this tutorial](https://github.com/ContinuumIO/gtc2018-numba) given at
the GPU Technology Conference 2018.
