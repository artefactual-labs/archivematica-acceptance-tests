from datetime import datetime, timedelta
import json
import pprint
import random

import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def datetime_string_to_datetime(datetime_string):
    dt, us = datetime_string.split('.')
    ret = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    us = int(us.rstrip("Z"), 10)
    return ret + timedelta(microseconds=us)


ds2d = datetime_string_to_datetime


EPOCH = datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return (dt - EPOCH).total_seconds() * 1000.0


def process_tasks(tasks):
    """Process a list of task dicts by sorting them according to their start times
    and returning 4 same-length iterables:
    1. the midpoints of each task (float)
    2. the durations of each task (float)
    3. the index of each task (given the temporal ordering)
    4. the type of each task
    """
    tasks_by_start_time = sorted([(ds2d(t['startTime']), t) for t in tasks])
    start_times = [s for s, t in tasks_by_start_time]
    print('\n'.join('{} {} {}'.format(t.isoformat(), mdates.date2num(t), unix_time_millis(t))
          for t in start_times))
    end_times = [ds2d(t['endTime']) for s, t in tasks_by_start_time]
    start_times = np.fromiter(
        (mdates.date2num(x) for x in start_times),
        dtype='float',
        count=len(start_times))
    end_times = np.fromiter(
        (mdates.date2num(x) for x in end_times),
        dtype='float',
        count=len(end_times))
    durations = end_times - start_times
    midpoints = [st + (0.5 * dur) for st, dur in zip(start_times, durations)]
    indices = [i + 1 for i in range(len(tasks))]
    task_types = [t['exec'] for t in tasks]
    return midpoints, durations, indices, task_types


def get_task_types_set(tasks):
    task_types = []
    for task in tasks:
        task_type = task['exec']
        if task_type not in task_types:
            task_types.append(task_type)
    return task_types


ALL_COLORS = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'orange',
              'black', 'brown', 'gray', 'fuchsia', 'gold', 'darkturquoise',
              'plum']


def get_task_type_color(tasks, task_type):
    task_types_set = get_task_types_set(tasks)
    task_type_index = task_types_set.index(task_type)
    return ALL_COLORS[task_type_index]


def human_task_type(tt):
    tt = tt.split('_')[0]
    new_tt = []
    for i, c in enumerate(tt):
        if c.lower() == c:
            new_tt.append(c)
        else:
            try:
                prevc = tt[i - 1]
            except IndexError:
                prevc = None
            try:
                nextc = tt[i + 1]
            except IndexError:
                nextc = None
            if not prevc or prevc.lower() == prevc or (nextc and nextc.lower() == nextc):
                new_tt.append(' ')
            new_tt.append(c.lower())
    return ''.join(new_tt)


def plot_tasks(tasks):
    fig = plt.figure(figsize=(20,10))
    ax = fig.add_subplot(1, 1, 1)
    midpoints, durations, indices, task_types = process_tasks(tasks)
    return
    ttseen = []
    linestyle = ''
    for middle, index, duration, task_type in zip(
            midpoints, indices, durations, task_types):
        color = get_task_type_color(tasks, task_type)
        linestyle = ''
        if task_type in ttseen:
            ax.errorbar(middle, index, xerr=duration, capthick=2, color=color,
                        linestyle=linestyle)
        else:
            ax.errorbar(middle, index, xerr=duration, capthick=2, color=color,
                        label=human_task_type(task_type), linestyle=linestyle)
            ttseen.append(task_type)
    plt.legend(loc='upper left')
    plt.show()
    plt.close('all')


def load_aip_stats(aip_stats_path):
    with open(aip_stats_path) as fi:
        return json.load(fi)


if __name__ == '__main__':
    aip_stats_path = 'data/with_outputs_stats-1512793137.json'
    aip_stats = load_aip_stats(aip_stats_path)
    tasks = aip_stats['tasks']
    plot_tasks(tasks)
