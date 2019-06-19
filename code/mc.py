import numpy as np
import csv
import argparse

def H(x):
    '''The Gaussian Hamiltonian x^2 used in this problem'''
    return x ** 2

def delta_H(x_old, x_new):
    '''The difference in Hamiltonian'''
    return H(x_new) - H(x_old)

def uniform_step(x, h):
    '''Returns a new x in the interval of width 2h around the current value'''
    return x + h * np.random.uniform(-h, h)

def metropolis(x, h, beta):
    '''A single Metropolis update for the Gaussian system'''
    x_new = uniform_step(x, h)
    
    exp_minusbetadeltaH = np.exp(-beta * delta_H(x, x_new))
    
    if exp_minusbetadeltaH > 1:
        return x_new, 1
    elif np.random.random() < exp_minusbetadeltaH:
        return x_new, 1
    else:
        return x, 0

def run_mc(x, h, beta, num_iterations, output_file):
    '''Run num_iterations Metropolis updates, and output the data to a file'''
    with open(output_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "accept"])

        for i in range(num_iterations):
            x, accept = metropolis(x, h, beta)
            writer.writerow([x, accept])

def main():
    parser = argparse.ArgumentParser(description="Runs Metropolis Monte Carlo")
    
    parser.add_argument("x0", type=float, help="Initial value for the state x")
    parser.add_argument("beta", type=float, help="Inverse temperature beta")
    parser.add_argument("h", type=float, help="Maximum step size in x")
    parser.add_argument("num_iterations", type=int, help="Number of steps to use")
    parser.add_argument("output_file", help="File to output x data to")

    args = parser.parse_args()

    run_mc(args.x0, args.h, args.beta, 
           args.num_iterations, args.output_file)

if __name__ == '__main__':
    main()
