---
title: "GNU Parallel for quick gains"
teaching: 20
exercises: 10
questions:
- "How and when do I use GNU Parallel with Python programs?"
objectives:
- Identify what sort of tasks are suitable for GNU Parallel to run in parallel
- Learn how to add command-line arguments to variables that GNU Parallel is to control
- Refresh how to use GNU Parallel to run in parallel a program that accepts command-line arguments
keypoints:
- Let your Python programs be controlled by command-line arguments so that GNU Parallel can run them in parallel
- Use `argparse` to let command-line arguments control your programs with relatively little work
---

Sometimes, you have a piece of software that processes one *thing*, and you
would like it to process many *thing*s. That *thing* may be anything&nbsp;an
image, a parameter set, a chunk of genetic data... The problem that you
have is that you have a script geared up to processing one *thing*, and
now you need to scale up to process many of them.

In many cases, the way
that you will approach this is to add a `for` loop around the block of
code, and iterate through a list (or other collection) of *thing*s.
This causes problems, however, if each *thing* takes more than a few minutes
to process, and you have many hundreds or thousands (or hundreds of
thousands!) of these *thing*s to process. Running all of these in a `for`
loop would take hours to days or weeks to run, and you can't rely on your
laptop being available for that long (or if you're already using
Supercomputing Wales, then the queue won't let you run for longer
than 3 days).

Fortunately, there is tooling available to help with this. Unlike the other
tools that will be discussed in the remainder of this lesson, this tool is
not Python-specific, and if you have previously taken the "Introduction
to High Performance Computing with Supercomputing Wales" course then you
will already have encountered it&mdash;it is GNU Parallel.

GNU Parallel takes a program, and runs it many times with a list of
possible inputs that you supply. It does this using as many cores as
are available on the node that you are using, and if you are using multiple
nodes, then with a little extra work then you can tell it to make use of
all available cores on all available nodes, too.

The only catch here is that your program must run without input, and be
able to run as a command-line script, accepting arguments to tell it
which *thing* to process. If at the moment you have a Jupyter notebook
that you hand-adjust each time you want to process a different *thing*,
then some changes will be needed to let you use GNU Parallel.


## Using command-line arguments

GNU Parallel uses command-line arguments to communicate to the many
different copies of your software that it runs. So in order to take
advantage of GNU Parallel to run your Python programs across many
different input files or sets of data, then it needs to be able to
accept command-line arguments for the parameters that you want GNU
Parallel to be able to control.

> ## Command line?
>
> If you're currently using a Jupyter Notebook for your analysis, you
> will need to convert it to running as an independent Python script
> in order to use GNU Parallel and command-line arguments. For more
> information on this, see the
> [Command-line arguments](http://swcarpentry.github.io/python-novice-inflammation/10-cmdline/)
> episode of the Software Carpentry Python lesson.
{: .callout}

A common pattern for quick Python programs is to hard-code a filename
or other parameter, and then adjust it by hand between runs. If you're
doing this at the moment, then you'll need to make a few changes to
your programs in order to take full advantage of the power that GNU
Parallel has to offer.

We are going to look at an example program `fourier_orig.py`, from the
code package you copied earlier. First off, try running this program to
see what it does:

~~~
$ python fourier_orig.py
~~~
{: .language-bash}

This should take a few seconds to run; use `ls -lrt` to see the most
recently created files in the directory once it finishes to see what
has been added. You will see that three PDF files
(`fourier_restricted.pdf`, `noise_isolation.pdf`, and `phase_contrast.pdf`)
have been created.

Next up, inspect the file in a text editor.

~~~
$ nano fourier_orig.py
~~~
{: .language-bash}

This program simulates a set of experiments in optics, where an image
is processed using a series of different manipulations. It reads in
an image file (currently `einstein1_7.jpg`), does some processing to it,
and outputs the three PDF files mentioned above, which are generated
independently of each other.

This program works fine for testing a single image, or
a handful, but for a full run of dozens or hundres of images, this is
too cumbersome to be practical. So, we would like to adjust the program
so that the filename to read can be controlled from the command line.

> ## A plan of attack
>
> Looking at `fourier_orig.py`, what sections of the program need to be
> changed in order for the program to be able to control the filename
> to read from the command-line? What other changes might need to be
> made so that the program will work properly in parallel when processing
> image files given as command-line arguments?
>
> Discuss your thoughts on this with one or more neighbours.
>
> > ## Solution
> >
> > To accept an image as a command-line argument, you will need:
> >
> > * To add an import in the first few lines, from a module that
> >   gives access to command line arguments
> > * To get the filename from the list of command line arguments and
> >   put it in a variable, somewhere before line 11
> > * To read from the given filename instead of from `einstein1_7.jpg`
> >   at line 11
> >
> > If this is run in parallel, the results files will always be
> > called the same name. So to make the program work in parallel,
> > you will additionally need to
> >
> > * Before lines 69, 132, and 153, either get three output filenames
> >   from the command-line arguments, or decide based on the input
> >   filename what the output filenames should be.
> > * At lines 69, 132, and 153, use the filenames from the previous
> >   bullet rather than the hard-coded ones that are currently used.
> > * If using command-line arguments for filenames, then decide what
> >   to do if the filenames are not provided. This could raise an
> >   error message, or could skip the step that was not given and not
> >   output anything.
> >
> > For this example, we will choose to specify the output filenames
> > as arguments, and skip steps that don't have an output file.
> {: .solution}
{: .challenge}

If you've worked through the
[Command-line programs](http://swcarpentry.github.io/python-novice-inflammation/10-cmdline/)
episode of the Software Carpentry Python lesson, you may remember that
you can use `sys.argv` to access the list of command-line arguments
passed to your program. However, this requires a lot of extra code to
handle edge cases and error checking if you want to do it robustly.
Instead, here we are going to use a module called `argparse` to parse
the command-line arguments for us. This module is part of the Python
standard library, so you don't need to install any additional packages
to make use of it.

To start off, make a copy of the file so you are not editing the original
program. You will need to press `Ctrl+X` if you are still inside `nano`
(or quit your editor if you are using a different one). Then

~~~
$ cp fourier_orig.py fourier_new.py
$ nano fourier_new.py
~~~
{: .language-bash}

Then add a line importing the part of the `argparse` module
that we are going to use, at the start of the file:

~~~
from argparse import ArgumentParser
~~~
{: .language-python}

Now, before the call to `plt.imread`, we need to use `ArgumentParser` to
get a filename to read. To do this, we will create an `ArgumentParser`
object, tell it what arguments we would like, and then tell it to get
them for us.

~~~
parser = ArgumentParser()
parser.add_argument('filename')
args = parser.parse_args()
~~~
{: .language-python}

With this done, `args` will hold any filename that gets supplied
as a command-line argument. Since in principle there can be more than one
argument, the filename will be an attribute of `args`.

Now, tell the call to `imread` to use this new filename by editing the line
to read:

~~~
image = plt.imread(args.filename)
~~~
{: .language-python}


At this point, the program should still do exactly what it did before,
provided the same input file is specified. Check that this is true, by
running:

~~~
python fourier_new.py einstein1_7.jpg
~~~
{: .language-bash}

If all is well, you will see no errors, and `ls -lrt` will show
that the three PDF files generated by the script have been updated.

We can now specify the input filename from the command line. If your
program only outputs to stdout (e.g. only outputs via `print`), and
you can tell from each line of output what the input parameters were,
then this is all you need to do, However, in the case of the Fourier
example, some output PDF files are also generated. We need to tell
the program where to put these so that they don't get overwritten by
subsequent runs of the program.

First off, before the call to `parse_args()`,
tell the `ArgumentParser` that we would like three more
arguments, and that they should be optional, with a default value of
`None`:

~~~
parser.add_argument('--fourier_restricted_output', default=None)
parser.add_argument('--noise_isolation_output', default=None)
parser.add_argument('--phase_contrast_output', default=None)
~~~
{: .language-python}

Now, after the call to `parse_args()`, the `args` objects will
have three extra attributes, representing the three optional arguments.
If they are not provided, then they are set to `None`.

The initial few lines are setup, and are needed for all three (or
at least more than one) of the tasks the program carries out.
From the line

~~~
# Move to Fourier plane
~~~
{: .language-python}

onwards is specific to each task. So, immediately before this line,
add a check as to whether the program is carrying out this task:

~~~
if args.fourier_restricted_output:
~~~
{: .language-python}

Indent everything up to the first call to `plt.savefig`, and change this
line to:

~~~
plt.savefig(args.fourier_restricted_output)
~~~
{: .language-python}

We can then repeat this step for the other two tasks that the program
carries out.

With this done, we can test that the program still works, by running:

~~~
$ python fourier_new.py einstein1_7.jpg \
      --fourier_restricted_output=fourier_restricted.pdf \
      --noise_isolation_output=noise_isolation.pdf \
      --phase_contrast_output=phase_contrast.pdf
~~~
{: .language-bash}

Again, `ls -lrt` will let you check that the output files are up to date.

With this done, we are now ready to use GNU Parallel to run this program
in parallel for many image files at once.


## Running your Python programs with GNU Parallel

Now that all the parameters that we want to control are exposed as
command-line arguments, we are ready to use GNU Parallel to run the
program across an entire batch of images at once.

To do this, let's create a new job script to let this run as a batch
job:

~~~
$ nano submit_fourier.sh
~~~
{: .language-bash}

~~~
#!/bin/bash --login
###
# Number of processors we will use
#SBATCH --ntasks 10
# Output file location
#SBATCH --output fourier.out.%J
# Time limit for this job
#SBATCH --time 00:10:00
# specify our current project
# change this for your own work
#SBATCH --account=scw1389
# specify the reservation we have for the training workshop
# remove this for your own work
# replace XX with the code provided by your instructor
#SBATCH --reservation=scw1389_18
###

# Ensure that parallel is available to us
module load parallel

# Load Python and activate the environment we will use for this work
module load anaconda/2019.03
source activate scw_test

# Only use one thread per copy of Python, since we are using GNU Parallel
# for parallelism
export OMP_NUM_THREADS=1

# Define srun arguments:
srun="srun --nodes 1 --ntasks 1"
# --nodes 1 --ntasks 1         allocates a single core to each task

# Define parallel arguments:
parallel="parallel --max-procs $SLURM_NTASKS --joblog parallel_joblog"
# --max-procs $SLURM_NTASKS  is the number of concurrent tasks parallel runs, so number of CPUs allocated
# --joblog name     parallel's log file of tasks it has run

# Run the tasks:
$parallel "$srun python fourier_new.py {1} \
    --fourier_restricted_output=fourier_restricted_\$(basename {1}).pdf \
    --noise_isolation_output=noise_isolation_\$(basename {1}).pdf \
    --phase_contrast_output=phase_contrast_\$(basename {1}).pdf" :::: files_to_process.txt
~~~
{: .bash}

This is adapted from the GNU Parallel script in the
[Supercomputing Wales tutorial](https://edbennett.github.io/SCW-tutorial).
The changes that we have made:
* The job requests 10 CPU cores rather than 80.
* The job now loads Anaconda and loads the tutorial environment we
  created earlier in the lesson
* The variable `OMP_NUM_THREADS` is set to 1. This is because
  Numpy will by default try and use all the cores available on a machine
  to do computation; this is great if it is the only copy running, but if
  we are trying to fill the CPU with parallel copies of the same program,
  then these would all end up competing for resources. Instead, we tell
  Numpy to only use a single thread per copy of Python, and let GNU Parallel
  do the work of filling up the CPU.
* The last line now calls our Python script rather than the
  `goostats` script from the Sotware Carpentry shell lesson

Set the reservation ID correctly (or remove it if you do not have a
reservation) and submit this job, and you should see a collection of PDF
files fill up your working directory.

> ## Getting more parallel
>
> Since we deliberately adjusted the Fourier program to let us specify
> which output files we wanted to generate, we can get more parallelism
> by running the three tasks in each job in parallel too.
>
> 1. How would you change `submit_fourier.sh` to parallelise this aspect
>    of the computation?
> 2. When would doing this give a speedup?
> 3. What would the disadvantages of this approach be?
>
> > ## Solution
> >
> > 1. The last line of the script would need to change, to add the
> >    operation to perform as an extra parameter to parallelise over.
> > 2. This would give a speedup when not all CPU cores are busy all the
> >    time. This would either be because there were fewer files to process
> >    than CPUs allocated to the job (10 in this case), or because some
> >    files took much longer than others to process, leaving some cores
> >    waiting for others to finish.
> > 3. The lines of code common to all tasks now run three times rather
> >    than one, limiting the speedup you will see. Profiling will help
> >    you understand how much of a problem this will be, but at a minimum
> >    the imports of libraries will take a couple of seconds each.
> {: .solution}
{: .challenge}

> ## More parameters
>
> The filenames are not the only parameters you could imagine wanting to
> tune for this program. Identify another variable that you may want to do
> a parameter sweep of, and adapt both `fourier_new.py` and
> `submit_fourier.sh` so that it does a parameter sweep of this
> variable instead of changing the image.
>
> Set the input image to `einstein1_7.jpg` in `submit_fourier.sh`
> rather than doing a full scan of all images, so that the job
> will finish in a reasonable time for today's lesson.
>
> In your research, there's nothing stopping you scanning multiple
> parameters at once like this, beyond the computational resource and
> time limits available on the machine.
{: .challenge}
