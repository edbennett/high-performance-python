---
title: "Profiling to identify bottlenecks"
teaching: 20
exercises: 15
questions:
- "Why is it important to know which parts of my software run slowly?"
- "How do I find out where to target optimisation effort?"
objectives:
- Be able to identify what functions and lines your program spends the most time on
- Use this information to guide approaches to optimisation
keypoints:
- Use the `cProfile` module to get an overview of where your program is spending time
- Save the results to a file and copy them to your machine to analyse them visually
- Check profiles again after optimisation to see whether it was successful
---


For the remainder of this workshop, we will be looking at ways to dig
deep into our Python code and adjust and tune it so that it goes
faster. Many of these methods take some amount of time to implement,
and may make the source code more difficult to read or maintain, so it
is important that we target optimisation where it is going to make a
difference&mdash;both so that we don't waste our time, and so that we
don't make our software harder to maintain in future.

For example, if you are working with a piece of simulation software
that performs a simulation and then plots the output, then the
simulation is probably going to take a lot longer than the plot. For
the sake of argument, say that the simulation is 99% of the time, and
the plot is the remaining 1%. No matter how much effort we spend
optimising the performance of the plotting section, even if we make it
run in no time whatsoever, we can only reduce the run time of the
software as a whole by 1%. Instead, a moderate optimisation of the
simulation part that decreased its run time by only 10% would decrease
the run time of the program as a whole by 9.9%&mdash;almost 10 times
better than the really difficult plotting optimisation.

Because of this, it's essential to know exactly where your software is
spending its time before you start spending time on optimising
it. Now, depending on your relationship with the software you are
trying to optimise, you may have some idea of where the bottlenecks
are, and where the software spends the bulk of its time. If you wrote
the software from scratch for example, you might have some strong
ideas about where to start looking. However, software has a nasty
tendency to bely our expectations about performance. Even domain
experts will swear up and down that they guarantee their software is
spending over 90% of its time in function X, only to be confronted
with hard data showing the program spending over 30% of its time in
function Y, in an entirely separate bit of code. This could be for any
number of reasons&mdash;perhaps the knowledge is based on a different
computer generation, with a different balance of performance of its
internal components, or perhaps it was based on a previous version of
the software, before an optimisation was found that trebled the speed
of the function that previously dominated.

No matter what you already know, it's crucial to have some good data
before starting optimisation. We need to use tools to help with this.
A piece of software that tells us where our software is spending its
time is called a *profiler*. A wide range of profilers is available on
the market, some free and some commercial, and each with its own
strengths and weaknesses.


## Using `cProfile` at the command line

Fortunately, Python comes with a profiler built in, which gives us
more than enough information to get us started optimising our
software.

`cProfile` is a built-in Python module, which can be run like a
program. It sits between the Python interpreter and your Python
program, intercepting each operation that Python does, and counting it
up for later analysis. Since it is a C extension (i.e. it is compiled,
not interpreted), it can do this while adding a minimum of overhead to
your Python programs.

Let's start by looking at `mc.py` from the code package you copied
earlier. This performs a small Monte Carlo simulation of a single
variable, saving the generated Markov Chain to a file, as well as some
metadata on what happened at each step. To run it without profiling,
type:

~~~
$ python mc.py 0 1.0 0.1 1000000 mc.dat
~~~
{: .language-bash}

This tells the program to start at zero, use a temperature of 1.0, a
step size of 0.1, to perform a million iterations, and to write the
resulting chain to the file `mc.dat`.

> ## Choosing your problem size
>
> It's important that the test that you profile runs long enough that
> it is not dominated by the time it takes to start the Python
> interpreter and load all of the libraries to run your
> program. Conversely, it's important for it not to run for so long
> that you have to walk away and get a coffee each time you make a
> change, since you'll want to run your profiling regularly as you
> change your program. The iteration count of 1,000,000 here is large
> enough that the program takes a few seconds to run. This is longer
> than most overheads, but short enough as to not be bothersome. 
>
> In
> your own applications, you may not be able to get the run time this
> low, but you want to aim for only a couple of minutes. If your
> current test case takes an hour to run, then think about assembling
> a smaller test case&emdash;while this will take some of your time,
> you would lose a lot more time waiting for your long test case to
> run every time you need an updated profile.
{: .callout}

To use `cProfile` to generate a profile for this program, add `-m
cProfile` after `python` and before the program name. (Note the capital
`P` in `cProfile`; without it, you will get an error.)

~~~
$ python -m cProfile mc.py 0 1.0 0.1 1000000 mc.dat
~~~
{: .language-bash}

This will output a long list of functions that are called during the
program's execution, most of which you never see because they are
internal to Python. Worse, most of the functions take no time to run
at all, or at least less than shows up on the output from `cProfile`.
We'd like to get an overview of the top hotspots where the program is
spending its time. To do this, we'll tell `cProfile` to sort by time;
for good measure, we'll also use the `head` command to only show the
first twenty lines of output.

~~~
$ python -m cProfile -s time mc.py 0 1.0 0.1 1000000 mc.dat 2> /dev/null | head -n 20
~~~
{: .language-bash}

> ## What the head?
>
> If the `| head` syntax is not familiar, then you may want to take a
> look at the 
> [Pipes and Filters](https://swcarpentry.github.io/shell-novice/04-pipefilter/) 
> episode of the
> [Software Carpentry tutorial on the Unix Shell](https://swcarpentry.github.io/shell-novice).
> For now, you can take it on trust that adding `| head -n 20` to the
> end of a command will make it output only the top 20 lines.
>
> The `2> /dev/null` addition tells Python to ignore any errors it
> encounters. `cProfile` by default doesn't behave nicely with `head`,
> so we tell it to suppress the error output.
{: .callout}

You'll now see a one-line report of what the program did
(specifically, call about 7.5 million functions in a few seconds), and
then a list of functions that got called in descending order of time
taken.

Taking a cursory look through these, the first call is the Metropolis
update algorithm, which is where we might expect a Metropolis Monte
Carlo program to spend its time. The second longest time however is
spent in the `writerow` method of `_csv.writer` objects. This program
does indeed write each line of output to disk using a CSV
writer&mdash;apparently this is quite expensive. Since this isn't the
core activity that this program is supposed to be doing, and is taking
a significant chunk of its runtime, then this might be a good target
for optimisation.

> ## Saving time on writes
>
> How might one go about improving the performance of writing to CSV
> in this kind of program? Discuss your thoughts in groups of two or
> three.
>
> If you're confident you've found a solution that will work, try
> implementing it in this program.
>
> > ## Solution
> >
> > The expense in going to disk is that the file has to be locked and
> > unlocked safely each time that it is written to. The volume of
> > data isn't a problem&mdash;this program only writes 22MB of data,
> > which shouuld take a lot less than two seconds&mdash; only the
> > number of individual writes (1,000,001) is.
> >
> > To reduce this number, one option is to group writes together, so
> > that the program keeps successive results in memory, only
> > outputting to disk every 100 or 1000 elements. This reduces the
> > number of calls to `_csv.writerow` by a factor of 100 or 1000,
> > which should make things run more snappily.
> {: .solution}
{: .challenge}

> ## Other sort options
>
> Other options for sorting the `cProfile` output are:
>
> * `calls` (call count)
> * `cumulative` (cumulative time)
> * `cumtime` (cumulative time)
> * `file` (file name)
> * `filename` (file name)
> * `module` (file name)
> * `ncalls` (call count)
> * `pcalls` (primitive call count)
> * `line` (line number)
> * `name` (function name)
> * `nfl` (name/file/line)
> * `stdname` (standard name)
> * `time` (internal time)
> * `tottime` (internal time)
>
> Try profiling `mc.py` again using the `cumtime` sort option.
> What is the difference between this and the `time` sort option we
> previously used?
>
> > ## Solution
> >
> > `cumtime` includes the time taken within function calls, while
> > `time` only includes the time taken within the function body
> > itself. This means that with `cumtime`, the main program will
> > always take the longest, and this time will be equal to the time
> > that the program executed for, whereas any function might appear
> > at the top of the list for `time`.
> {: .solution}
{: .challenge}


## Viewing `cProfile` results graphically

Frequently when displaying results as plain text, or in a table, we
don't see the full picture; for this reason, we tend to utilise graphs
and other visualisations when viewing the results of
computations. Profiling works exactly the same way&mdash;while the
text-mode profile is very useful in itself, we can get more
information out of the profile by using a visualisation tool.

While `cProfile` doesn't itself include any visualisation tooling, it
will save its output into a file so that other tools can display it.

SnakeViz is one tool that we can use to look at the profile data from
a different angle. To start, re-run the program, but now save the
profile to a file rather than outputting it to the display.

~~~
$ python -m cProfile -o mc.prof mc.py 0 1.0 0.1 1000000 mc.dat
~~~
{: .language-bash}

This will create a file called `mc.prof`, containing the profiling
data. Now, since displaying graphics from the cluster on your own
machine isn't always easy, instead we'll copy the profile to our local
machine to view. This can be done with FileZilla, or at a Bash prompt.


To do this at the shell, open a new terminal (running on your own
machine), and run the command:

~~~
$ # This runs on your computer, not on the supercomputer
$ scp s.your.username@sunbird.swansea.ac.uk:high-performance-python-examples/mc.prof ~/Desktop/
~~~
{: .language-bash}

Now we can install SnakeViz and visualise the profile:

~~~
$ # This should also happen on your own computer
$ pip install snakeviz
$ snakeviz ~/Desktop/mc.prof
~~~
{: .language-bash}

This should automatically open a web browser window with the profile
result. If the window doesn't open, the terminal output will indicate
where you can point your browser to load the result. Once the result
is loaded, you can press Ctrl+C in the terminal window to stop
SnakeViz.

The results show the same data that was in the full profile we saw
initially, but now it is organised so that it is much easier to read
what times include each other. You can also see what sort of time the
many tiny function calls in the original profile add up to. For this
small example, the overhead of starting a Python interpreter and
loading the required modules is still quite large compared to the
total run time, so if we wanted to run many such examples, we would gain
speed by using Pathos rather than GNU Parallel&mdash;see this
aftenroon's session.


## Using `timeit` for quick and dirty timings

Sometimes you don't need a full profile; all you're interested in is
how long one particular operation takes. While you could use the Unix
`time` function to get this for you, Python provides a more precise
alternative. The `timeit` module will run a particular expression or
line of code repeatedly, to get a good estimate of how long it takes.
This removes the overhead of starting Python from the problem.

To use `timeit` at the command line, use `python -m timeit` followed
by the expression you want to time. For example,

~~~
$ python -m timeit 'x = [i ** 2 for i in range(1000)]'
~~~
{: .language-bash}

will measure how long it takes to calculate a particular list
comprehension.

> ## List comprehension?
>
> If you've not encountered a list comprehension before, this syntax
> provides a one-line way to construct a list. The result is
> equivalent to the loop:
>
> ~~~
> x = []
> for i in range(1000):
>     x.append(i ** 2)
> ~~~
> {: .language-python}
>
> However, the list comprehension will normally be quicker.
{: .callout}

The output will tell you how many times Python ran the code to get an
average:

~~~
1000 loops, best of 3: 265 usec per loop
~~~
{: .output}

If you want to test an operation that involves a library function, you
can import that library outside of the timed region. (Since normally
you load libraries once at the start of a program, but use a function
a lot, you are not normally interested in the load time of the
library.) To do this, pass the operations to run before the timed
region with the `--setup` option. For example, to look at the
`metropolis` function from the Monte Carlo code above:

~~~
$ python -m timeit --setup 'import mc' 'mc.metropolis(1.0, 0.1, 1.0)'
~~~
{: .language-bash}

> ## Comparing the loop with the list comprehension
>
> We asserted above that the list comprehension would be quicker than
> the loop. But at the top of this episode we said that we should test
> our assertions about performance, not rely on common wisdom. Check
> how the run time of the loop version of the list comprehension code
> compares.
>
> > ## Solution
> >
> > On my computer, the list comprehension takes 265 microseconds per
> > iteration, while the loop takes 312 microseconds&mdash;a whopping
> > 18% slower!
> {: .solution}
{: .challenge}

> ## `timeit` magic in Jupyter notebooks
>
> You can use `timeit` within a Jupyter notebook to test the
> performance of code you are writing there, too. In a new cell, use
> `%timeit` followed by the function or expresion you want to time,
> and use `%%timeit` at the top of a cell to time the execution of the
> entire cell.
>
> If you have Jupyter installed on your machine, open a new notebook
> and try this now for the list comprehension and loop
> comparison. Do the timings match up with what you see at the command
> line?
{: .challenge}
