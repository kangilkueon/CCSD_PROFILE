#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import regex as re
import math
import gantt

import logging
gantt.init_log_to_sysout(level=logging.CRITICAL)

# Format 
# [TIME] [CCSD_PROFILE] [WORKER_#_TASKNAME_START(or END)]
worker_list=[]
items = []
f = open("sample.txt", 'r')
lines = f.readlines()
for line in lines:
    line = re.sub('\[\s+', '[', line)
    #print(line)
    line = line.split()
    #print(line)
    if len(line) == 3:
        if line[1] == "[CCSD_PROFILE]":
            words = line[2].split('_')
            if len(words) > 3:
                #print(words)
                if words[len(words) - 1] == 'START':
                    task_type = words[0]
                    worker_name = words[0] + '_' + words[1]
                    if worker_name not in worker_list:
                        worker_list.append(worker_name)

                    idx = line[0].find(']')
                    time = line[0][1:idx]

                    task_name = words[2]
                    if len(words) > 5:
                        task_name = task_name + '_' + words[3] + '_' + words[4]

                    items.append({'task_type':task_type, 'worker_name':worker_name, 'task_name':task_name, 'start':time, 'end':0})
                if words[len(words) - 1] == 'END':
                    task_type = words[0]
                    worker_name = words[0] + '_' + words[1]
                    task_name = words[2]
                    if len(words) > 5:
                        task_name = task_name + '_' + words[3] + '_' + words[4]
                        
                    if worker_name not in worker_list:
                        worker_list.append(worker_name)

                    idx = line[0].find(']')
                    time = line[0][1:idx]

                    for item in items[::-1]:
                        if item['task_type'] == task_type and item['task_name'] == task_name and item['end'] == 0:
                            item['end'] = time
                            break
f.close()

# Change font default
gantt.define_font_attributes(fill='black', stroke='black', stroke_width=0, font_family="Verdana")

#print("len : ", len(items))
start_time = float(items[0]['start'])
end_time = float(items[len(items) - 1]['end'])
#print(start_time)
#print(end_time)

worker_object = []
for worker in worker_list:
    p = gantt.Project(name=worker)
    worker_object.append({'name':worker, 'object':p})
#print(worker_list)
p = gantt.Project(name='CCSD')
# find Min term
min = 0xFFFFFFFF
max = 0

for item in items:
    duration = (float(item['end']) - float(item['start'])) * 1000000
    if min > duration and duration > 0:
        min = duration
    if max < duration:
        max = duration

#print("d", min)
for item in items:
    start = ((float(item['start']) - start_time) * 1000000 / min)
    duration = ((float(item['end']) - float(item['start'])) * 1000000 / min)
    task = gantt.Task(name=item['task_name'], start=start, duration=duration)

    for worker in worker_object:
        if worker['name'] == item['worker_name']:
            worker['object'].add_task(task)
            break

for po in worker_object:
    p.add_task(po['object'])

p.make_svg_for_tasks(filename='test_full.svg', start=0, end=int((end_time - start_time) / min * 1000000))