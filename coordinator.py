# -*- coding: UTF-8 -*-

""" Coordinator runs codes in different stages
"""

import argparse
import importlib
import copy
import subprocess
import os
import logging
import json
import datetime
import time
import re
import threading

result_pattern = re.compile('-->([^<>-]+)<--')

dump_run = False

def dump_runner(cmds, dump):
    time.sleep(0.5)
    while dump_run:
        for cmd in cmds:
            dump_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            while True:
                line = dump_proc.stdout.readline()
                if line != '':
                    dump.write(line)
                else:
                    break
            dump.write('==========\n')

class Coordinator:
    def __init__(self, config, output, dump):
        self.config = config
        self.output = output
        self.dump = dump

    def _run_next(self, exp):
        global dump_run
        this_env = {}
        if 'env' in self.config:
            this_env.update(self.config['env'])
        if 'env' in exp:
            this_env.update(exp['env'])
        print 'running experiment {}'.format(exp['name'])
        env = ' '.join(map(lambda x: '='.join(map(str, x)), this_env.iteritems()))
        cmd = self.config['cmd'].replace('<ENV>', env)
        print('[debug] executing: %s' % cmd)
        self.dump.write('>>>>> {} dump starts\n'.format(exp["name"]))
        self.dump.write('==========\n')
        dump_run = True
        dump_thread = threading.Thread(target=dump_runner, args=(self.config['monitor_cmds'], self.dump))
        dump_thread.start()
        tasks = exp.get('tasks', 1)
        processes = [subprocess.Popen(cmd, shell=True) for _ in range(tasks)]
        for process in processes:
            process.wait()
        dump_run = False
        result_per_exp = exp.get('result_per_exp', self.config['result_per_exp'])
        print('[debug] execution finished')
        print('[debug] writing last {} result(s) into result log'.format(result_per_exp))
        print('[debug] waiting for dump runner to stop')
        dump_thread.join()
        print('[debug] dump runner stopped')
        self.output.write(exp['name'])
        self.output.write('\n')
        results = []
        log_proc = subprocess.Popen(self.config['log_cmd'], stdout=subprocess.PIPE, shell=True)
        while True:
            line = log_proc.stdout.readline()
            if line != '':
                for result in re.findall(result_pattern, line):
                    results.append(result)
            else:
                break
        self.output.write(','.join(results[-result_per_exp:]))
        self.output.write('\n')

        # subprocess.call(cmd, shell=True)

    def run(self):
        print 'Start running experiments ------ {}'.format(self.config['description'])
        self.output.write('Experiment at {}\n'.format(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")))
        for exp in self.config['exps']:
            self._run_next(exp)


def main():
    parser = argparse.ArgumentParser(description='coordinate multiple processes')
    parser.add_argument('config', help='config to use')
    parser.add_argument('output', help='output file to write to')
    parser.add_argument('dump', help='dump file to write to')
    result = parser.parse_args()
    dump_file = open(result.dump, 'a')
    with open(result.config) as config_file:
        with open(result.output, 'a') as output_file:
            cood = Coordinator(json.load(config_file), output_file, dump_file)
            cood.run()
    dump_file.close()

if __name__ == '__main__':
    main()
