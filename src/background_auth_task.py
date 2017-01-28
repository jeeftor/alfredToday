# encoding: utf-8
import sys
from query_exchange import asrun, asquote
from workflow import Workflow3, ICON_INFO
import subprocess
from today import  get_cache_key
from workflow.background import run_in_background, is_running

import os
from signal import SIGTERM, SIGKILL

from workflow.background import is_running, _pid_file

def kill(job_name, force=False):
    """Kill a job started by `background.run_in_background()`."""
    if is_running(job_name):
        # Read PID from file created by `run_in_background()`
        pid = int(open(_pid_file(job_name)).read().strip())
        # Default to asking nicely
        sig = SIGTERM
        if force:  # Die, die, die!
            sig = SIGKILL

        os.kill(pid, sig)
        # Not strictly necessary to remove the now stale PID file,
        # as `is_running()` will do it on the next call


def main(wf):


    if is_running('auth'):
        log.info('!!WARNING!!! Background Authorization is already running!! - Attempting KILL')
        kill('auth', force=True)


    log.info('Launching bg task')

    run_in_background('auth',
              ['/usr/bin/python',
               wf.workflowfile('src/wf_authorize_google.py')])



if __name__ == '__main__':
    wf = Workflow3(libraries=['./lib'])
    log = wf.logger
    log.debug('        ___   __  __________  __')
    log.debug('       /   | / / / /_  __/ / / /')
    log.debug('      / /| |/ / / / / / / /_/ /')
    log.debug('     / ___ / /_/ / / / / __  /')
    log.debug('    /_/  |_\____/ /_/ /_/ /_/')
    log.debug('          GOOGLE Calendar')
    log.debug('')

    sys.exit(wf.run(main))
