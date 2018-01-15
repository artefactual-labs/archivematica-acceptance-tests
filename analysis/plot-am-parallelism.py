#! /usr/bin/env python

from datetime import datetime, timedelta
import json
import pprint
import sys

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


def unix_time_micros(dt):
    return (dt - EPOCH).total_seconds() * 1000000.0


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
    end_times = [ds2d(t['endTime']) for s, t in tasks_by_start_time]
    start_times = [unix_time_micros(t) for t in start_times]
    end_times = [unix_time_micros(t) for t in end_times]
    durations = [e - s for s, e in zip(start_times, end_times)]
    midpoints = [st + (0.5 * dur) for st, dur in zip(start_times, durations)]
    indices = [i + 1 for i in range(len(tasks))]
    task_types = [t['exec'] for t in tasks]
    return start_times, end_times, midpoints, durations, indices, task_types


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


def get_total_aip_processing_time(start_times, end_times):
    s = min(start_times)
    e = max(end_times)
    t = e - s
    return t


def get_total_serialized_task_processing_time(start_times, end_times):
    """Return the total number of task processing seconds, i.e., the runtime if
    all tasks were executed serially.
    """
    return sum(e-s for s, e in zip(start_times, end_times))


def get_total_task_processing_time(start_times, end_times):
    """Return the total number of microseconds where task processing was
    occurring. If there are two tasks A and B and task A started at 0 and ended
    at 1000, and task B started at 500 and ended at 1200, the return value
    would be 1200.
    """
    interval_start = None
    interval_end = None
    intervals = []
    start_time = min(start_times)
    for start, end in zip(start_times, end_times):
        if interval_start is None and interval_end is None:
            interval_start = start
            interval_end = end
            continue
        if start > interval_end:
            intervals.append((interval_start, interval_end))
            interval_start = start
        interval_end = end
    intervals.append((interval_start, interval_end))
    return sum(e-s for s, e in intervals)


def get_longest_task(start_times, end_times):
    return max(e-s for s, e in zip(start_times, end_times))


def plot_tasks(tasks):
    fig = plt.figure(figsize=(20,10))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title('Archivematica AIP Creation: concurrency view')
    ax.set_xlabel('Time (microseconds)')
    ax.set_ylabel('Task indices')
    start_times, end_times, midpoints, durations, indices, task_types = (
        process_tasks(tasks))
    total_aip_proc_time = get_total_aip_processing_time(start_times, end_times)
    total_task_proc_time = get_total_task_processing_time(
        start_times, end_times)
    total_serial_task_proc_time = get_total_serialized_task_processing_time(
        start_times, end_times)
    print('total_aip_proc_time')
    print('{} seconds'.format(total_aip_proc_time * 0.000001))
    print(type(total_aip_proc_time))
    print('total_task_proc_time')
    print('{} seconds'.format(total_task_proc_time * 0.000001))
    print(type(total_task_proc_time))
    print('total_serial_task_proc_time')
    print('{} seconds'.format(total_serial_task_proc_time * 0.000001))
    print(type(total_serial_task_proc_time))
    longest_task = get_longest_task(start_times, end_times)
    print('longest_task')
    print('{} seconds'.format(longest_task * 0.000001))
    print(type(longest_task))
    x = total_task_proc_time / total_serial_task_proc_time
    print(x)
    ttseen = []
    linestyle = ''
    start = min(start_times)
    for middle, index, duration, task_type in zip(
            midpoints, indices, durations, task_types):
        color = get_task_type_color(tasks, task_type)
        linestyle = ''
        middle = middle - start
        kwargs = {
            'xerr': duration / 2,
            'yerr': 0.1,
            'color': color,
            'capsize': 0,
            'linestyle': linestyle,
            'elinewidth': 3
        }
        if task_type not in ttseen:
            kwargs['label'] = human_task_type(task_type)
            ttseen.append(task_type)
        ax.errorbar(middle, index, **kwargs)
    plt.legend(loc='upper left')
    plt.show()


def load_aip_stats(aip_stats_path):
    with open(aip_stats_path) as fi:
        return json.load(fi)


if __name__ == '__main__':
    aip_stats_path = sys.argv[1]
    aip_stats = load_aip_stats(aip_stats_path)
    tasks = aip_stats['tasks']
    plot_tasks(tasks)
