---
title: "Numpy (and Scipy)"
teaching: 50
exercises: 25
questions:
- "How can I use Numpy to go faster on a single core?"
- "To what extent can Numpy exploit multiple cores?"
- "What can Scipy do to help in all this?"
---

Earlier this morning we discussed how one source of overhead in Python
is that it needs to store a whole lot of metadata about what data type
it is, among other things. This gets worse when we start storing lots
of data in a single data structure. For example, to store a 
1000&times;1000 grid of values, this would require a list of lists,
with a million total elements, each with more metadata than data. 
This is in part because lists can store any kind of data, not only
data of the same type. But most frequently when dealing with these
large objects, the values will in fact all be the same sort of data. 
It would seem prudent to try and find a data structure that doesn't
need all of this extra metadata on every value, and instead stores it
once for the entire object. Python comes with this built in; it is
called an "array". Unfortunately, Python arrays aren't especially
useful&mdash;they store the data efficiently, but don't give many
useful operations on them, and so the community has developed an
alternative.

## Numpy

Numpy (short for **Num**erical **Py**thon) has the answer. Numpy
provides a data structure called an `ndarray` (short for
*N*-dimensional array). Unlike Python arrays (which must be
one-dimensional, like lists), `ndarray`s can have any number of
dimensions, making them useful for all kinds of data. Numpy also
provides a large number of functions that do useful things to
arrays. (If you have followed the Software Carpentry Python lesson, you
have already encountered Numpy, as it is used there to load data from
text files.)

You might recall from earlier in the morning that one of the
properties of Python that limits performance is that when doing
operations on sequences of numbers, the data type metadata means that
the processor can't efficiently vectorise the computation. Now, since
`ndarray`s remove the metadata, one would expect that the operations
can now be vectorised, and so would run faster.

Let's compare the list comprehension from the previous episode to the
equivalent Numpy functions.

~~~
$ python -m timeit 'x = [i**2 for i in range(1000)]'
$ python -m timeit --setup='import numpy as np' 'x = np.arange(1000) ** 2'
~~~
{: .language-bash}

> ## `np`?
>
> You'll notice above that the `numpy` module has been imported as
> `np`. This is a very common convention when using Numpy in Python;
> it has the advantage of significantly reducing the amount of typing
> needed to use Numpy functions.
{: .callout}

The `arange` function is the Numpy equivalent of Python's `range`,
with some extra functionality. Unlike `range`, which returns a
generator, `arange` returns an `ndarray`. Depending on your computer,
you may see that the second version here is around 100 times faster
than the first. This is clearly not just vectorisation&mdash;the most
speedup you'd expect there is around 8&times;. Instead, Numpy
implements operations across the whole array with high-speed loops in
a compiled programming language, rather than using Python's slower
loops.

### Broadcasting and whole-array operations in Numpy

This highlights one of Numpy's most powerful features. In Numpy,
operations on arrays are applied to the whole array, element-wise. 
For example, in the example above we squared an array; this returned
the array containing the squared numbers&mdash;the numbers being the
same as those generated in the list comprehension. The single number
to the right of the `**` has been *broadcast* to act on all the
elements in the `ndarray`.

This also works with arithmetic operations between arrays. You can,
for example, add two arrays together, or multiply their elements, and
Numpy will perform the operations as efficiently as it knows how.

The key point is that the operations must be these whole-array or
broadcast operations in order to gain this speed. If you try to use a
normal Python `for` loop over elements of an `ndarray`, this will most
likely perform even slower than the equivalent loop over a Python
list, since Numpy needs to do some extra bookkeeping compared to
Python.

Let's look at another example, and see how we can use whole-array
operations to improve its performance. The Euclidean distance between
two vectors $p_i$ and $q_i$ in an $N$-dimensional space is given by:

$$D(p, q) = \sqrt{\sum_{i=1}^{N} \left| p_i - q_i \right|^2}$$


If we hadn't heard of Numpy, we might treat $p_i$ and $q_i$ as lists,
and use the following function to calculate the distance:

~~~
def naive_dist(p, q):
    square_distance = 0
    for p_i, q_i in zip(p, q):
        square_distance += (p_i - q_i) ** 2
    return square_distance ** 0.5
~~~
{: .language-python}

Let's save this function in a file `dist.py`, and time it for some
example 1000-element vectors.

~~~
$ python -m timeit --setup='import dist; p = [i for i in range(1000)]; \
    q = [i + 2 for i in range(1000)]' \
    'dist.naive_dist(p, q)'
~~~
{: .language-bash}

~~~
1000 loops, best of 3: 299 usec per loop
~~~
{: .output}

How might we do this with Numpy? Well, we know that Numpy can subtract
and square whole vectors at once, so let's take advantage of that. It
also offers a whole-array function for a summation (the `sum`
function).

~~~
import numpy as np

def simple_numpy_dist(p, q):
    return (np.sum((p - q) ** 2)) ** 0.5
~~~
{: .language-python}

Add this function definition to the `dist.py` file we just made.
To time this, we need to do the setup with Numpy rather than with list
comprehensions, since otherwise Python will complain when it tries to
subtract two lists. We'll use `arange` here to generate a some test
data, but the performance should be the same no matter how the input
data are generated, provided the data type is the same.

~~~
$ python -m timeit --setup='import dist; import numpy as np; \
    p = np.arange(1000); q = np.arange(1000) + 2' \
    'dist.simple_numpy_dist(p, q)'
~~~
{: .language-bash}

~~~
100000 loops, best of 3: 9.96 usec per loop
~~~
{: .output}

This is a factor of thirty improvement, but can we do better? Since
the length of a vector is a very common operation, Numpy in fact
provides a built-in function for it: `np.linalg.norm`. Using that:

~~~
def numpy_norm_dist(p, q):
    return np.linalg.norm(p - q)
~~~
{: .language-python}

Adding this to `dist.py` and timing it again reveals:

~~~
100000 loops, best of 3: 7.34 usec per loop
~~~
{: .output}

That's a 26% improvement on the previous case, and a 41x improvement
on the original naive code!

### Multiple dimensions

For one-dimensional arrays, translating from naive to whole-array
operations is normally quite direct. But when it comes to
multi-dimensional arrays, some additional work may be needed to get
everything into the right shape.

Let's extend the previous example to work on multiple vectors at
once. We would like to calculate the Euclidean distances between $M$
pairs of vectors, each of length $N$. In plain Python we could take
this as a list of lists, and re-use the previous function for each
vector in turn.

~~~
def naive_dists(ps, qs):
    return [naive_dist(p, q) for p, q in zip(ps, qs)]
~~~
{: .language-python}

Adjusting the timing code to create a list of lists now:

~~~
$ python -m timeit --setup='import dist; \
    ps = [[i + 1000 * j for i in range(1000)] for j in range(1000)]; \
    qs = [[i + 1000 * j + 2 for i in range(1000)] for j in range(1000)]' \
    'dist.naive_dists(ps, qs)'
~~~
{: .language-bash}

~~~
10 loops, best of 3: 311 msec per loop
~~~
{: .output}

Now this is starting to be some more serious lifting&mdash;almost a
third of a second per iteration.

Moving this to Numpy, we can subtract as we did previously, but for
the summation, we need to be able to tell Numpy to leave us
with a one-dimensional array of distances, rather than a single
number. To do this, we pass the `axis` keyword argument, which tells
Numpy which axis to sum over. In this case, axis 0 controls which
vector we are selecting, and axis 1 controls which element of the
vector. Thus here we only want to sum over axis 1, leaving axis 0
still representing the vector of sums.

~~~
def simple_numpy_dists(ps, qs):
    return np.sum((ps - qs) ** 2, axis=1) ** 0.5
~~~
{: .language-python}

To test the performance of this, we need to generate the same sample
data we previously used. Rather than trying to build up the array
element by element, it is more efficient to build it as a list, and
then convert the list to an array with `np.asarray()`.

~~~
$ python -m timeit --setup='import numpy as np; \
    import dist; \
    ps = np.asarray([[i + 1000 * j \
                      for i in range(1000)] \
                     for j in range(1000)]); \
    qs = np.asarray([[i + 1000 * j + 2 \
                      for i in range(1000)] \
                     for j in range(1000)])' \
    'dist.simple_numpy_dists(ps, qs)'
~~~
{: .language-bash}

~~~
100 loops, best of 3: 3.29 msec per loop
~~~
{: .output}

Once again we've achieved almost a 100x speedup by switching over to
Numpy. What about the `norm` function we tried previously? This also
supports the `axis` keyword argument.

~~~
def numpy_norm_dists(ps, qs):
    return np.linalg.norm(ps - qs, axis=1)
~~~
{: .language-python}

Timing this gives:

~~~
100 loops, best of 3: 4.65 msec per loop
~~~
{: .output}

Unlike the 1-dimensional case, using the dedicated `norm` function
provided by Numpy is slower here than the explicit computation! As you
can see, it's always important to test your improvements on data that
resemble those that you will be performing your computation on, as the
performance characteristics will change from case to case.

Numpy does have one more trick up its sleeve, however...


### Einsum

The problem with these more complex cases is that we're having to use
optional arguments to `np.sum` and `np.linalg.norm`. By necessity,
Numpy can't optimise all cases of these general functions as well as
it would be able to optimise the specific case that we are interested
in.

Numpy does give us a way to express an exact reduction that we would
like to perform, and can execute it in a highly optimised way. The
function that does this is `np.einsum`, which is short for "Einstein
summation convention". If you're not familiar with this, it is a
notation used in physics for abbreviating common expressions that have
many summations in them.

`np.einsum` requires as arguments a string specifying the operations
to be carried out, and then the array(s) that the operations will be
carried out on. The string is formatted in a specific way: indices to
look up (starting from `i`, `j`, `k`, ...) are given for each array,
separated by commas, followed by `->` (representing an arrow), and
then the indices for the resulting array are given. Any indices not on
the right-hand side are summed over.

For example, `'ii->i'` gives a one-dimensional array (or a vector)
containing the diagonal elements of a two-dimensional array (or
matrix). This is because the $i$th element of this vector contains the
element $(i, i)$ of the matrix.

In this case, we want to calculate the array's product with itself,
summing along axis 1. This can be done via `'ij,ij->i'`, although the
array will need to be given twice or this to work. Because of this,
we'll need to put the difference array into a variable before passing
it into `np.einsum`. Putting this together:

~~~
def einsum_dists(ps, qs):
    difference = ps - qs
    return np.einsum('ij,ij->i', difference, difference) ** 0.5
~~~
{: .language-python}

Timing this:

~~~
1000 loops, best of 3: 1.7 msec per loop
~~~
{: .output}

Wow! At the expense of some readability, we've gained another factor
of 2 in performance. Since the resulting line of code is significantly
harder to read, and any errors in the `np.einsum` syntax are likely to
be impenetrable, it is important to leave a comment explaining exactly
what you are trying to do with this syntax when you use it. That way,
if someone (yourself included) comes back to it in six months, they
will have a better idea of what it does, and can double-check that it
does indeed do this. And if there is a bug, you can check whether the
bug is in the design (was the line trying to do the wrong thing) or in
the implementation (was it trying to do the right thing, but the
`np.einsum` syntax for that thing was implemented wrong).

`np.einsum` is best used sparingly, at the most performance-critical
parts of your program. Used well, though, it can be a game-changer,
since it can express many operations that would be difficult to
express any other way without using explicit `for` loops.

> ## Calculating Pi
>
> A common example problem in numerical computing is the Monte Carlo
> computation of $\pi$. The way this works is as follows.
>
> Consider the
> unit circle, centered on the origin. Now, imagine firing bullets at
> random locations in the square from the origin to the point (1,
> 1). The area of that square that overlaps with the circle is
> $\frac{\pi}{4}$, while the area of the square is 1. So the
> proportion of bullets that will land in the circle is
> $\frac{\pi}{4}$.
>
> So, by generating a large number of random points in the unit
> square, and counting the number that lie within the unit circle, we
> can find an estimate for $\frac{\pi}{4}$, and by extension, $\pi$.
>
> A plain Python function that would achieve this might look as
> follows:
>
> ~~~
> from random import random
>
> def naive_pi(number_of_samples):
>     within_circle_count = 0
>
>     for _ in range(number_of_samples):
>         x = random()
>         y = random()
>
>         if x ** 2 + y ** 2 < 1:
>             within_circle_count += 1
>
>     return within_circle_count / number_of_samples * 4
> ~~~
> {: .language-python}
>
> Time this for a million iterations. Check that it gives the correct
> result for $\pi$.
>
> Try and convert this to Numpy. Think about how you can utilise
> whole-array operations. Time your result and see how it compares to
> the plain Python case. How much faster can you get?
>
> You'll want to use `np.random.random` for your random numbers. Take
> a look at the documentation for that function to see what arguments
> it takes that will be helpful for this problem.
{: .challenge}


> ## Multiple cores?
>
> Many functions in Numpy will try to take advantage of multi-core
> parallelism in your machine. While this is better than ignoring
> parallelism completely, it isn't perfect. In many cases there is no
> speedup from the parallel implementation; and many functions aren't
> parallelised at all.
>
> Something to beware is that if you try and take advantage of
> parallelism yourself via, for example, GNU Parallel, then Numpy
> might not be aware of this, and will try and use every CPU core you
> have available&mdash;for every copy of the program that is
> executing. While the parallelism may not have sped things up much,
> this will severely slow down all of your programs, since the
> processor is spending most of its time swapping between different
> threads rather than doing actual work.
>
> If you do want multi-core parallelism out of your Numpy code, it's
> better to do it more explicitly as we'll explore in a later section.
>
> To disable Numpy's parallelism, you need to set the environment
> variable `OMP_NUM_THREADS` to 1 before launching your program.
{: .callout}


## Scipy

Science is done by standing on the shoulders of giants. The majority
of the work that we do is using techniques that are well-established,
and algorithms that have been around for years if not decades. So, the
majority of the time, we don't want to write all of our software from
scratch using the basic functions that Numpy provides, since getting
the ideal performance from this would take considerable work. Instead,
we would like to use an implementation that a group of talented
developers ahve written and spent a lot of time optimising to run as
fast as possible. This is what Scipy provides; built on top of Numpy,
it interfaces with a wide range of C and Fortran libraries to provide
a core of essential algorithms in scientific computing.

If Numpy was too large to explore in detail in this episode, then
the same applies ten times as much for Scipy. The principle to operate
on is before writing a function or other block of code, ask yourself
if it's something that others from multiple disciplines are likely to
have needed to do. If so, then take yourself to your nearest internet
search engine, and have a look to see if such a function exists in
Scipy, or even elsewhere.

Modules that Scipy provides include:

* *constants*: physical constants and conversion factors
* *cluster*: hierarchical clustering, vector quantization, K-means
* *fftpack*: Discrete Fourier Transform algorithms
* *integrate*: numerical integration routines, solution of
  differential equations
* *interpolate*: interpolation tools
* *io*: data input and output
* *lib*: Python wrappers to external libraries
* *linalg*: linear algebra routines
* *misc*: miscellaneous utilities (e.g. image reading/writing)
* *ndimage*: various functions for multi-dimensional image processing
* *optimize*: optimization algorithms, e.g. curve fitting and
  regression analysis
* *signal*: signal processing tools
* *sparse*: sparse matrix and related algorithms
* *spatial*: KD-trees, nearest neighbors, distance functions
* *special*: special functions
* *stats*: statistical functions

It is worth noting that while Scipy provides a generally performant,
very comprehensive baseline, it is not necessarily the absolute
fastest software in every case. Due to the license it uses, it cannot
incorporate all libraries that are available to you as Python
programmers. For example, the routines `scipy.fftpack` are relatively
slow for certain types of matrix; for this reason, the Fourier optics
example used earlier this morning uses a drop-in compatible
replacement that makes use of the *FFTW* ("Fastest Fourier Transform
in the West") library, which as the name suggests, is the fastest
available.
