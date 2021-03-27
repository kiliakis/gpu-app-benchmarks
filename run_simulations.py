#!/usr/bin/env python

from optparse import OptionParser
import os
import subprocess
import sys
import re
import datetime
import yaml
import common

this_directory = os.path.dirname(os.path.realpath(__file__)) + "/"
# This function will pull the SO name out of the shared object,
# which will have current GIT commit number attatched.

# parser = argparse.ArgumentParser(description='Run the GPU experiments locally.',
#                                  usage='python script.py -o results')


# parser.add_argument('-o', '--output', type=str, default='./results/',
#                     help='Output directory to store the output data. Default: ./results/')

# parser.add_argument('-b', '--benchmark_file', type=str,
#                     help='The yaml file used to define which benchmarks are run.')

# parser.add_argument('-c', '--configs_file', type=str,
#                     help='configs_file used to determine which nvprof options are extracted.')
# nvprof_params = {
#     'nvprof': [],
#     '-m':
#     # ['achieved_occupancy',
#     #        'ipc', 'issue_ipc', 'stall_exec_dependecy',
#     #        'stall_memory_dependency', 'stall_pipe_busy',
#     #        'stall_other', 'stall_sync'
#     #        ],
#     '-e':
#     # ['elapsed_cycles_sm', 'elapsed_cycles_pm',
#     #        'active_warps_pm', 'active_cycles_pm',
#     #        'inst_issued0', 'inst_executed',
#     #        'sm_cta_launched'],
#     '--csv': []
# }
nvprof_params = ['nvprof', '-e', 'all', '-m', 'all', '--csv']

now_time = datetime.datetime.now()
day_string = now_time.strftime("%d.%m.%y")
time_string = now_time.strftime("%H.%M.%S")


#######################################################################################
# Class the represents each configuration you are going to run
# For example, if your sweep file has 2 entries 32k-L1 and 64k-L1 there will be 2
# ConfigurationSpec classes and the run_subdir name for each will be 32k-L1 and 64k-L1
# respectively
class ConfigurationSpec:
    #########################################################################################
    # Public Interface methods
    #########################################################################################
    # Class is constructed with a single line of text from the sweep_param file
    def __init__(self, (name, params, config_file)):
        self.run_subdir = name
        self.params = params
        self.config_file = config_file

    def my_print(self):
        print "Run Subdir = " + self.run_subdir
        print "Parameters = " + self.params
        print "Base config file = " + self.config_file

    def run(self, benchmarks, run_directory, cuda_version):
        for dir_bench in benchmarks:
            exec_dir, run_dir, benchmark, self.command_line_args_list = dir_bench
            full_exec_dir = os.path.join(this_directory, exec_dir)
            full_run_dir = os.path.join(this_directory, run_dir, benchmark)

            self.benchmark_args_subdirs = {}
            for args in self.command_line_args_list:
                # print args
                if args == "" or args == None:
                    self.benchmark_args_subdirs[args] = "NO_ARGS"
                else:
                    self.benchmark_args_subdirs[args] = re.sub(
                        r"[^a-z^A-Z^0-9]", "_", args.strip())

            for args in self.command_line_args_list:
                this_run_dir = run_directory +\
                    "/" + benchmark + "/" + self.benchmark_args_subdirs[args] +\
                    "/" + self.run_subdir + "/"
                self.setup_run_directory(full_run_dir, this_run_dir)

                # Submit the job to torque and dump the output to a file
                if not options.no_launch:
                    saved_dir = os.getcwd()
                    os.chdir(this_run_dir)
                    outfile = 'stdout.txt'
                    errfile = 'stderr.txt'
                    exe_args = nvprof_params + \
                        [os.path.join(full_exec_dir, benchmark)]
                    if args is not None:
                        exe_args += [args]
                    print("Running: " + ' '.join(exe_args))
                    if subprocess.call(exe_args,
                                       stdout=open(outfile, 'w'),
                                       stderr=open(errfile, 'w')) < 0:
                        exit("Error running nvprof")
                    else:
                        # Parse the torque output for just the numeric ID
                        print("Job run ("
                              + benchmark + "-"
                              + self.benchmark_args_subdirs[args]
                              + " " + self.run_subdir + ")")
                    os.chdir(saved_dir)

                    # Dump the benchmark description to the logfile
                    if not os.path.exists(this_directory + "logfiles/"):
                        os.makedirs(this_directory + "logfiles/")
                    log_name = "sim_log.{0}".format(options.launch_name)
                    logfile = open(this_directory
                                   + "logfiles/" + log_name + "."
                                   + day_string
                                   + "-" + time_string + ".txt", 'a')
                    print >> logfile, "%s %6s %-22s %-100s %-25s %s.%s" %\
                        (time_string,
                         # torque_out,
                         benchmark,
                         self.benchmark_args_subdirs[args],
                         self.run_subdir,
                         benchmark)
                    logfile.close()
            self.benchmark_args_subdirs.clear()

    #########################################################################################
    # Internal utility methods
    #########################################################################################
    # copies and links the necessary files to the run directory
    def setup_run_directory(self, full_bin_dir, this_run_dir):
        if not os.path.isdir(this_run_dir):
            os.makedirs(this_run_dir)

        # link the data directory
        if os.path.isdir(os.path.join(full_bin_dir, "data")):
            if os.path.lexists(os.path.join(this_run_dir, "data")):
                os.remove(os.path.join(this_run_dir, "data"))
            os.symlink(os.path.join(full_bin_dir, "data"),
                       os.path.join(this_run_dir, "data"))


if __name__ == '__main__':
    # -----------------------------------------------------------
    # main script start
    # -----------------------------------------------------------
    (options, args) = common.parse_run_simulations_options()

    cuda_version = common.get_cuda_version()

    if options.run_directory == "":
        options.run_directory = os.path.join(
            this_directory, "./bench_run_%s" % cuda_version)
    else:
        options.run_directory = os.path.join(os.getcwd(), options.run_directory)

    # Let's copy out the .so file so that builds don't interfere with running tests
    # If the user does not specify a so file, then use the one in the git repo and copy it out.

    # Test for the existance of nvcc on the system
    if not any([os.path.isfile(os.path.join(p, "nvcc")) for p in os.getenv("PATH").split(os.pathsep)]):
        exit("ERROR - Cannot find nvcc PATH... Is CUDA_INSTALL_PATH/bin in the system PATH?")

    options.benchmark_file = common.file_option_test(options.benchmark_file,
                                                     os.path.join(
                                                         this_directory, "regression_recipies", "rodinia_2.0-ft", "benchmarks.yml"),
                                                     this_directory)
    benchmarks = common.parse_app_yml(options.benchmark_file)
    # cfgs = common.parse_config_yml(options.configs_file)
    cfgs = [('default', 'base', 'extra')]
    configurations = []
    for config in cfgs:
        configurations.append(ConfigurationSpec(config))

    print("Running Benchmarks"
          # + "\nUsing configs_file " + options.configs_file
          + "\nBenchmark File " + options.benchmark_file)

    for config in configurations:
        config.my_print()
        config.run(benchmarks, options.run_directory, cuda_version)
