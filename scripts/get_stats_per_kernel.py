#!/usr/bin/env python
from optparse import OptionParser
import re
import os
import csv

# *********************************************************--
# main script start
# *********************************************************--
this_directory = os.path.dirname(os.path.realpath(__file__)) + "/"

help_str = "There is 1 way to use this file" +\
           " 1) Specify the run dir: \"-r <the run directory>\"\n"


parser = OptionParser(usage=help_str)
parser = OptionParser()
parser.add_option("-r", "--run_dir", dest="run_dir",
                  help="The directory where the benchmark/config directories exist.", default="")


parser.add_option("-f", "--file", dest="file", default="",
                  help="The output file name.")


events = [
    'achieved_occupancy', 'ipc',
    'issue_ipc', 'stall_exec_dependecy',
    'stall_memory_dependency', 'stall_pipe_busy',
    'stall_other', 'stall_sync',
    'elapsed_cycles_sm', 'elapsed_cycles_pm',
    'active_warps_pm', 'active_cycles_pm',
    'inst_issued0', 'inst_executed',
    'sm_cta_launched', 'warps_launched'
]

header = ["device", "kernel", "invocations",
          "event", "min", "max", "avg", "total"]
regexp = re.compile(r'\"(.*)\",\"(.*)\",(\d+),\"(.*)\",(.*),(.*),(.*),(.*)')
outheader = ['app_and_args', 'config', 'metric', 'num_kernels', 'valuelist']

if __name__ == '__main__':
    (options, args) = parser.parse_args()
    options.run_dir = options.run_dir.strip()
    if options.run_dir[-1] == '/':
        options.run_dir = options.run_dir[:-1]

    if not os.path.isdir(options.run_dir):
        exit(options.run_dir +
             " does not exist - specify the run directory where the benchmark/config dirs exist")

    if options.file == '':
        options.file = options.run_dir.split('/')[-1]
    if not os.path.isdir(os.path.join(this_directory, '../results/csvfiles/')):
        os.makedirs(os.path.join(this_directory, '../results/csvfiles/'))
    options.file = '{}../results/csvfiles/kernel-stats-{}.csv'.format(
        this_directory, options.file)

    rows = [outheader]
    for root, dirs, files in os.walk(options.run_dir):
        if 'stderr.txt' not in files:
            continue
        # here we have found our input file
        # first extract the needed app_args, etc
        app_and_arg = root.split('/')[-3:-1]
        app_and_arg = '/'.join(app_and_arg)
        # now I am ready to iterate over the file
        print("Checking root: " + root)
        dic = {}
        for line in open(os.path.join(root, 'stderr.txt'), 'r'):
            match = regexp.match(line)
            if match:
                dev, kernel, invoc, event, mine, maxe, avge, totale = match.groups()
                kernel = kernel.split('(')[0].split('<')[0]
                if ' ' in kernel:
                    kernel = kernel.split(' ')[1]
                mine = mine.replace('%', '')
                maxe = maxe.replace('%', '')
                avge = avge.replace('%', '')
                totale = totale.replace('%', '')
                dev = dev.split('(')[0].replace(' ', '').split('-')[0]
                if event not in dic:
                    dic['event'] = []
                dic['event'] += [totale] * int(invoc)

                if 'kernel_name' not in dic:
                    dic['kernel_name'] = []
                # if kernel not in dic['kernel_name']:
                #     dic['kernel_name'] += [kernel] * int(invoc)

                #     kernels.append(kernel)
                #     kernelrow = [app_and_arg, dev, 'kernel_name',
                #            invoc, '|'.join(([kernel] * int(invoc)))]
                #     rows.append(row)
                # row = [app_and_arg, dev, event, invoc,
                #        '|'.join(([totale] * int(invoc)))]
                # rows.append(row)
        for k,v in dic.iteritems():
            num_kernels = len(v)
            row = [app_and_arg, dev, k, num_kernels, '|'.join(v)]
            rows.append(row)
            
    writer = csv.writer(open(options.file, 'w'), delimiter='\t')
    writer.writerows(rows)

    # options.stats_yml = common.file_option_test(options.stats_yml, os.path.join(this_directory, "../stats", "base_stats.yml"),
    #                                             this_directory)

    # configs = set()
    # apps_and_args = set()
    # specific_jobIds = {}

    # stats_to_pull = {}
    # stats_yaml = yaml.load(open(options.stats_yml))
    # stats = {}
    # all_regexp = []
    # stats_list = []
    # for stat in stats_yaml['collect']:
    #     stats_to_pull[stat] = stats_yaml['collect'][stat]
    #     all_regexp.append(stats_yaml['collect'][stat])
    #     stats_list.append(stat)

    # all_regexp = re.compile('|'.join(all_regexp))

    # # if options.configs_yml != "" and options.apps_yml != "":
    # #     for app in common.parse_app_yml(options.apps_yml):
    # #         a, b, exe_name, args_list = app
    # #         for args in args_list:
    # #             apps_and_args.add(os.path.join(exe_name, re.sub(
    # #                 r"[^a-z^A-Z^0-9]", "_", args.strip())))
    # #     for config, params, gpuconf_file in common.parse_config_yml(options.configs_yml):
    # #         configs.add(config)
    # # else:
    # # This code gets the logfiles to pull the stats from if you are using the "-l" or "-N" option
    # parsed_logfiles = []
    # logfiles_directory = this_directory + "../job_launching/logfiles/"
    # if options.logfile == "":
    #     if not os.path.exists(logfiles_directory):
    #         exit("No logfile specified and the default logfile directory cannot be found")
    #     all_logfiles = [os.path.join(logfiles_directory, f)
    #                     for f in os.listdir(logfiles_directory) if(re.match(r'sim_log.*', f))]
    #     if len(all_logfiles) == 0:
    #         exit("ERROR - No Logfiles in " + logfiles_directory)
    #     if options.sim_name != "":
    #         named_sim = []
    #         for logf in all_logfiles:
    #             match_str = r".*\/sim_log\.{0}\..*".format(options.sim_name)
    #             if re.match(match_str, logf):
    #                 named_sim.append(logf)
    #         if len(named_sim) == 0:
    #             exit("Could not find logfiles for job with the name \"{0}\"".format(
    #                 options.sim_name))
    #         all_logfiles = named_sim
    #     parsed_logfiles.append(max(all_logfiles, key=os.path.getmtime))
    # elif options.logfile == "all":
    #     parsed_logfiles = [os.path.join(logfiles_directory, f)
    #                        for f in os.listdir(logfiles_directory) if(re.match(r'sim_log.*\.latest', f))]
    # else:
    #     parsed_logfiles.append(common.file_option_test(
    #         options.logfile, "", this_directory))

    # # print "Using logfiles " + str(parsed_logfiles)

    # for logfile in parsed_logfiles:
    #     if not os.path.isfile(logfile):
    #         exit("Cannot open Logfile " + logfile)

    #     with open(logfile) as f:
    #         for line in f:
    #             time, jobId, app, args, config, jobname = line.split()
    #             configs.add(config)
    #             app_and_args = os.path.join(app, args)
    #             apps_and_args.add(app_and_args)
    #             specific_jobIds[config + app_and_args] = jobId

    # row = ['app_and_args', 'config', 'metric', 'num_kernels', 'valuelist']

    # # step=100
    # if options.file != 'stdout':
    #     # rows = []
    #     writer = csv.writer(open(options.file, 'w'), delimiter='\t')
    #     writer.writerow(row)
    # else:
    #     print '{:<25.25}\t{:<20.20}\t{:<20.20}\t{:<4}\t{:<50.50}'.format(*row)

    # for app_and_args in apps_and_args:
    #     for config in configs:
    #         stat_map = {}
    #         # now get the right output file
    #         output_dir = os.path.join(options.run_dir, app_and_args, config)
    #         if not os.path.isdir(output_dir):
    #             print("WARNING the outputdir " + output_dir + " does not exist")
    #             continue

    #         if config + app_and_args in specific_jobIds:
    #             jobId = specific_jobIds[config + app_and_args]
    #             outfile = glob.glob(
    #                 '{}/{}.o{}*'.format(output_dir, app_and_args.replace('/', '-'), jobId))
    #             if len(outfile):
    #                 outfile = outfile[0]
    #             else:
    #                 outfile = '{}/{}.o{}*'.format(output_dir,
    #                                               app_and_args.replace('/', '-'), jobId)
    #             # outfile = os.path.join(output_dir, app_and_args.replace("/", "-") + "." + "o" + jobId)
    #         else:
    #             all_outfiles = [os.path.join(output_dir, f)
    #                             for f in os.listdir(output_dir) if(re.match(r'.*\.o[0-9]+', f))]
    #             outfile = max(all_outfiles, key=os.path.getmtime)

    #         # stat_found = set()

    #         if not os.path.isfile(outfile):
    #             print "WARNING - " + outfile + " does not exist"
    #             continue

    #         # Do a quick 100-line pass to get the GPGPU-Sim Version number
    #         MAX_LINES = 100
    #         count = 0
    #         if 'bz2' in outfile:
    #             openfile = bz2.BZ2File(outfile, 'r')
    #         else:
    #             openfile = open(outfile, 'r')

    #         lines = openfile.readlines()
    #         openfile.close()

    #         for line in lines:
    #             count += 1
    #             if count >= MAX_LINES:
    #                 break
    #             build_match = re.match(".*\[build\s+(.*)\].*", line)
    #             if build_match:
    #                 stat_map["GPGPU-Sim-build"] = [build_match.group(1)]
    #                 break

    #         # Only go up for 10000 lines looking for stuff
    #         # MAX_LINES = 100000
    #         # count = 0

    #         for line in lines:
    #             # pull out some stats
    #             existance_test = all_regexp.findall(line)
    #             if existance_test:
    #                 for match in existance_test:
    #                     # print(match)
    #                     for i, number in enumerate(match):
    #                         if number:
    #                             stat_name = stats_list[i]
    #                             if stat_name not in stat_map:
    #                                 stat_map[stat_name] = []
    #                             stat_map[stat_name].append(number.strip())
    #                             break

    #         for stat_name in stats_to_pull:
    #             row = [app_and_args, config, stat_name]
    #             if stat_name in stat_map:
    #                 row.append(len(stat_map[stat_name]))
    #                 row.append('|'.join(stat_map[stat_name]))
    #             else:
    #                 row += ['0', 'nan']
    #             # rows.append(row)
    #             if options.file != 'stdout':
    #                 writer.writerow(row)
    #                 # rows.append(row)
    #             else:
    #                 print '{:<25.25}\t{:<20.20}\t{:<20.20}\t{:<4}\t{:<50.50}'.format(*r)

    # if options.file != 'stdout':
    #     if options.compress:
    #         np.savez_compressed(options.file, np.array(rows, str))
    #     else:
    #         np.savez(options.file, np.array(rows, str))
