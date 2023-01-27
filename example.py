#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import regex as re
import gantt

import logging
gantt.init_log_to_sysout(level=logging.CRITICAL)

worker_list=[]
items = []
f = open("sample.txt", 'r')
lines = f.readlines()
for line in lines:
    print(line)
    line = line.split()
    print(line)
    if len(line) == 3:
        if line[1] == "[CCSD_PROFILE]":
            words = line[2].split('_')
            if len(words) == 6:
                if words[5] == 'START':
                    worker_name = words[0] + '_' + words[1]
                    if worker_name not in worker_list:
                        worker_list.append(worker_name)

                    idx = line[0].find(']')
                    time = line[0][1:idx]

                    task_name = words[2] + '_' + words[3] + '_' + words[4]
                    items.append({'worker_name':worker_name, 'task_name':task_name, 'start':time, 'end':0})
                if words[5] == 'END':
                    worker_name = words[0] + '_' + words[1]
                    task_name = words[2] + '_' + words[3] + '_' + words[4]
                    if worker_name not in worker_list:
                        worker_list.append(worker_name)

                    idx = line[0].find(']')
                    time = line[0][1:idx]

                    for item in items[::-1]:
                        if item['worker_name'] == worker_name and item['task_name'] == task_name and item['end'] == 0:
                            item['end'] = time
                            break
f.close()

print(items)
# Change font default
gantt.define_font_attributes(fill='black', stroke='black', stroke_width=0, font_family="Verdana")

start_time = float(items[0]['start'])
end_time = float(items[len(items) - 1]['end'])
print(start_time)
print(end_time)

worker_object = []
for worker in worker_list:
    p = gantt.Project(name=worker)
    worker_object.append({'name':worker, 'object':p})

for item in items:
    start = (float(item['start']) - start_time) * 1000000
    duration = (float(item['end']) - float(item['start'])) * 1000000

    task = gantt.Task(name=item['task_name'], start=(start + 10), duration=duration)

    for worker in worker_object:
        if worker['name'] == item['worker_name']:
            worker['object'].add_task(task)
            break



p = gantt.Project(name='CCSD')
for po in worker_object:
    p.add_task(po['object'])

p.make_svg_for_tasks(filename='test_full.svg', start=0, end=int((end_time - start_time) * 2000000))