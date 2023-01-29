#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gantt.py - version and date, see below

This is a python class to create gantt chart using SVG


Author : Alexandre Norman - norman at xael.org
Licence : GPL v3 or any later version


This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

__author__ = 'Alexandre Norman (norman at xael.org)'
__version__ = '0.5.0'
__last_modification__ = '2016.02.01'

import codecs
import datetime
import logging
import sys
import types

# https://bitbucket.org/mozman/svgwrite
# http://svgwrite.readthedocs.org/en/latest/

import svgwrite
# conversion from mm/cm to pixel is done by ourselve as firefox seems
# to have a bug for big numbers...
# 3.543307 is for conversion from mm to pt units !
mm = 3.543307
cm = 35.43307


# https://labix.org/python-dateutil
import dateutil.relativedelta


class _my_svgwrite_drawing_wrapper(svgwrite.Drawing):
    """
    Hack for beeing able to use a file descriptor as filename
    """
    def save(self, width='100%', height='100%'):
        """ Write the XML string to **filename**. """
        test = False
        import io

        # Fix height and width
        self['height'] = height
        self['width'] = width
        
        if sys.version_info[0] == 2:
            test = type(self.filename) == types.FileType or type(self.filename) == types.InstanceType
        elif sys.version_info[0] == 3:
            test = type(self.filename) == io.TextIOWrapper

        if test:
            self.write(self.filename)
        else:
            fileobj = io.open(str(self.filename), mode='w', encoding='utf-8')
            self.write(fileobj)
            fileobj.close()



############################################################################

__LOG__ = None

############################################################################

DRAW_WITH_DAILY_SCALE = 'd'
DRAW_WITH_WEEKLY_SCALE = 'w'
DRAW_WITH_MONTHLY_SCALE = 'm'
DRAW_WITH_QUATERLY_SCALE = 'q'

############################################################################

# Unworked days (0: Monday ... 6: Sunday)
NOT_WORKED_DAYS = [5, 6]


def define_not_worked_days(list_of_days):
    """
    Define specific days off

    Keyword arguments:
    list_of_days -- list of integer (0: Monday ... 6: Sunday) - default [5, 6]
    """
    global NOT_WORKED_DAYS
    NOT_WORKED_DAYS = list_of_days
    return


def _not_worked_days():
    """
    Returns list of days off (0: Monday ... 6: Sunday)
    """
    global NOT_WORKED_DAYS
    return NOT_WORKED_DAYS


############################################################################

FONT_ATTR = {
    'fill': 'black',
    'stroke': 'black',
    'stroke_width': 0,
    'font_family': 'Verdana',
    'font_size': 15
    }


def define_font_attributes(fill='black', stroke='black', stroke_width=0, font_family="Verdana"):
    """
    Define font attributes
    
    Keyword arguments:
    fill -- fill - default 'black'
    stroke -- stroke - default 'black'
    stroke_width -- stroke width - default 0
    font_family -- font family - default 'Verdana'
    """
    global FONT_ATTR

    FONT_ATTR = {
        'fill': fill,
        'stroke' : stroke,
        'stroke_width': stroke_width,
        'font_family': font_family, 
        }

    return


def _font_attributes():
    """
    Return dictionnary of font attributes
    Example :
    FONT_ATTR = {
      'fill': 'black',
      'stroke': 'black',
      'stroke_width': 0,
      'font_family': 'Verdana',
    }
    """
    global FONT_ATTR
    return FONT_ATTR


############################################################################


# list of vacations as datetime (non worked days)
VACATIONS = []


############################################################################


def add_vacations(start_date, end_date=None):
    """
    Add vacations to a resource begining at [start_date] to [end_date]
    (included). If [end_date] is not defined, vacation will be for [start_date]
    day only

    Keyword arguments:
    start_date -- datetime.date begining of vacation
    end_date -- datetime.date end of vacation of vacation
    """
    __LOG__.debug('** add_vacations {0}'.format({'start_date':start_date, 'end_date':end_date}))

    global VACATIONS
    
    if end_date is None:
        if start_date not in VACATIONS:
            VACATIONS.append(start_date)
    else:
        while start_date <= end_date:
            if start_date not in VACATIONS:
                VACATIONS.append(start_date)
                
            start_date += datetime.timedelta(days=1)

    __LOG__.debug('** add_vacations {0}'.format({'start_date':start_date, 'end_date':end_date, 'vac':VACATIONS}))

    return

############################################################################

def init_log_to_sysout(level=logging.INFO):
    """
    Init global variable __LOG__ used for logging purpose

    Keyword arguments:
    level -- logging level (from logging.debug to logging.critical)
    """
    global __LOG__
    logger = logging.getLogger("Gantt")
    logger.setLevel(level)
    fh = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    __LOG__ = logging.getLogger("Gantt")
    return

############################################################################

def _show_version(name, **kwargs):
    """
    Show version
    """
    import os
    print("{0} version {1}".format(os.path.basename(name), __version__))
    return True


############################################################################


def _flatten(l, ltypes=(list, tuple)):
    """
    Return a flatten list from a list like [1,2,[4,5,1]]
    """
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

############################################################################

class Task(object):
    """
    Class for manipulating Tasks
    """
    def __init__(self, name, start=None, stop=None, duration=None, depends_of=None, resources=None, percent_done=0, color=None, fullname=None, display=True, state=''):
        """
        Initialize task object. Two of start, stop or duration may be given.
        This task can rely on other task and will be completed with resources.
        If percent done is given, a progress bar will be included on the task.
        If color is specified, it will be used for the task.

        Keyword arguments:
        name -- name of the task (id)
        fullname -- long name given to the resource
        start -- datetime.date, first day of the task, default None
        stop -- datetime.date, last day of the task, default None
        duration -- int, duration of the task, default None
        depends_of -- list of Task which are parents of this one, default None
        resources -- list of Resources assigned to the task, default None
        percent_done -- int, percent of achievment, default 0
        color -- string, html color, default None
        display -- boolean, display this task, default True
        state -- string, state of the task
        """
        __LOG__.debug('** Task::__init__ {0}'.format({'name':name, 'start':start, 'stop':stop, 'duration':duration, 'depends_of':depends_of, 'resources':resources, 'percent_done':percent_done}))
        self.name = name
        if fullname is not None:
            self.fullname = fullname
        else:
            self.fullname = name

        self.start = start
        self.stop = stop
        self.duration = duration
        self.color = color
        self.display = display
        self.state = state

        ends = (self.start, self.stop, self.duration)
        nonecount = 0
        for e in ends:
            if e is None:
                nonecount += 1

        # check limits (2 must be set on 4) or scheduling is defined by duration and dependencies
        if nonecount != 1 and  (self.duration is None or depends_of is None):
            __LOG__.error('** Task "{1}" must be defined by two of three limits ({0})'.format({'start':self.start, 'stop':self.stop, 'duration':self.duration}, fullname))
            # Bug ? may be defined later
            #raise ValueError('Task "{1}" must be defined by two of three limits ({0})'.format({'start':self.start, 'stop':self.stop, 'duration':self.duration}, fullname))

        if type(depends_of) is type([]):
            self.depends_of = depends_of
        elif depends_of is not None:
            self.depends_of = [depends_of]
        else:
            self.depends_of = None

        self.resources = resources
        self.percent_done = percent_done
        self.drawn_x_begin_coord = None
        self.drawn_x_end_coord = None
        self.drawn_y_coord = None
        self.cache_start_date = None
        self.cache_end_date = None

        return


    def add_depends(self, depends_of):
        """
        Adds dependency to a task

        Keyword arguments:
        depends_of -- list of Task which are parents of this one
        """
        if type(depends_of) is type([]):
            if self.depends_of is None:
                self.depends_of = depends_of
            else:
                for d in depends_of:
                    self.depends_of.append(d)
        else:
            if self.depends_of is None:
                self.depends_of = depends_of
            else:
                self.depends_of.append(depends_of)

        return


    def start_date(self):
        """
        Returns the first day of the task, either the one which was given at
        task creation or the one calculated after checking dependencies
        """
        if self.cache_start_date is not None:
            return self.cache_start_date

        __LOG__.debug('** Task::start_date ({0})'.format(self.name))
        if self.start is not None:
            # start date setted, calculate begining
            if self.depends_of is None:
                # depends of nothing... start date is start
                #__LOG__.debug('*** Do not depend of other task')
                start = self.start
                while start.weekday() in _not_worked_days() or start in VACATIONS:
                    start = start + datetime.timedelta(days=1)

                if start > self.start:
                    __LOG__.warning('** Due to vacations, Task "{0}", will not start on date {1} but {2}'.format(self.fullname, self.start, start))

                self.cache_start_date = start
                return self.cache_start_date
            else:
                # depends of other task, start date could vary
                #__LOG__.debug('*** Do depend of other tasks')
                start = self.start
                while start.weekday() in _not_worked_days() or start in VACATIONS:
                    start = start + datetime.timedelta(days=1)

                prev_task_end = start
                for t in self.depends_of:
                    if isinstance(t, Milestone):
                        if t.end_date() >= prev_task_end:
                            prev_task_end = t.end_date()
                    elif isinstance(t, Task):
                        if t.end_date() >= prev_task_end:
                            prev_task_end = t.end_date() + datetime.timedelta(days=1)

                while prev_task_end.weekday() in _not_worked_days() or prev_task_end in VACATIONS:
                    prev_task_end = prev_task_end + datetime.timedelta(days=1)

                if prev_task_end > self.start:
                    __LOG__.warning('** Due to dependencies, Task "{0}", will not start on date {1} but {2}'.format(self.fullname, self.start, prev_task_end))

                self.cache_start_date = prev_task_end
                return self.cache_start_date

        elif self.duration is None: # start and stop fixed
            current_day = self.start
            # check depends
            if self.depends_of is not None:
                prev_task_end = self.depends_of[0].end_date()
                for t in self.depends_of:
                    if isinstance(t, Milestone):
                        if t.end_date() > prev_task_end:
                            prev_task_end = t.end_date() - datetime.timedelta(days=1)
                    elif isinstance(t, Task):
                        if t.end_date() > prev_task_end:
                            prev_task_end = t.end_date()
                    # if t.end_date() > prev_task_end:
                    #     #__LOG__.debug('*** latest one {0} which end on {1}'.format(t.name, t.end_date()))
                    #     prev_task_end = t.end_date()
                if prev_task_end > current_day:
                    depend_start_date = prev_task_end
                else:
                    start = self.start
                    while start.weekday() in _not_worked_days() or start in VACATIONS:
                        start = start + datetime.timedelta(days=1)
                    depend_start_date = start

                    if depend_start_date > current_day:
                        __LOG__.error('** Due to dependencies, Task "{0}", could not be finished on time (should start as last on {1} but will start on {2})'.format(self.fullname, current_day, depend_start_date))
                    self.cache_start_date = depend_start_date           
            else:
                # should be first day of start...
                self.cache_start_date = current_day            

            return self.cache_start_date

        elif self.duration is not None and self.depends_of is not None and self.stop is None :  # duration and dependencies fixed
            prev_task_end = self.depends_of[0].end_date()
            for t in self.depends_of:
                if isinstance(t, Milestone):
                    if t.end_date() > prev_task_end:
                        prev_task_end = t.end_date() - datetime.timedelta(days=1)
                elif isinstance(t, Task):
                    if t.end_date() > prev_task_end:
                        prev_task_end = t.end_date()
                # if t.end_date() > prev_task_end:
                #     __LOG__.debug('*** latest one {0} which end on {1}'.format(t.name, t.end_date()))
                #     prev_task_end = t.end_date()

            start = prev_task_end + datetime.timedelta(days=1)
            
            while start.weekday() in _not_worked_days() or start in VACATIONS:
                start = start + datetime.timedelta(days=1)

            # should be first day of start...
            self.cache_start_date = start

        elif self.start is None and self.stop is not None: # stop and duration fixed
            # start date not setted, calculate from end_date + depends
            current_day = self.stop
            real_duration = 0
            duration = self.duration 
            while duration > 0:
                if not (current_day.weekday() in _not_worked_days() or current_day in VACATIONS):
                    real_duration = real_duration + 1
                    duration -= 1
                else:
                    real_duration = real_duration + 1

                current_day = self.stop - datetime.timedelta(days=real_duration)
            current_day = self.stop - datetime.timedelta(days=real_duration - 1)

            # check depends
            if self.depends_of is not None:
                prev_task_end = self.depends_of[0].end_date()
                for t in self.depends_of:
                    if isinstance(t, Milestone):
                        if t.end_date() > prev_task_end:
                            prev_task_end = t.end_date()
                    elif isinstance(t, Task):
                        if t.end_date() > prev_task_end:
                            prev_task_end = t.end_date()
                    # if t.end_date() > prev_task_end:
                    #     __LOG__.debug('*** latest one {0} which end on {1}'.format(t.name, t.end_date()))
                    #     prev_task_end = t.end_date()

                if prev_task_end > current_day:
                    start = prev_task_end + datetime.timedelta(days=1)
                    #return prev_task_end
                else:
                    start = current_day

                
                while start.weekday() in _not_worked_days() or start in VACATIONS:
                    start = start + datetime.timedelta(days=1)

                depend_start_date = start

                if depend_start_date > current_day:
                    __LOG__.error('** Due to dependencies, Task "{0}", could not be finished on time (should start as last on {1} but will start on {2})'.format(self.fullname, current_day, depend_start_date))
                    self.cache_start_date = depend_start_date           
                else:
                    # should be first day of start...
                    self.cache_start_date = depend_start_date
            else:
                # should be first day of start...
                self.cache_start_date = current_day            


        if self.cache_start_date != self.start:
            __LOG__.warning('** starting date for task "{0}" is changed from {1} to {2}'.format(self.fullname, self.start, self.cache_start_date))
        return self.cache_start_date


    def end_date(self):
        """
        Returns the last day of the task, either the one which was given at task
        creation or the one calculated after checking dependencies
        """
        # Should take care of resources vacations ?
        if self.cache_end_date is not None:
            return self.cache_end_date

        __LOG__.debug('** Task::end_date ({0})'.format(self.name))

        if self.duration is None or self.start is None and self.stop is not None:
            real_end = self.stop
            # Take care of vacations
            while real_end.weekday() in _not_worked_days() or real_end in VACATIONS:
                real_end -= datetime.timedelta(days=1)

            if real_end <= self.start_date():
                current_day = self.start_date()
                real_duration = 0
                duration = self.duration   
                while duration > 1 or (current_day.weekday() in _not_worked_days() or current_day in VACATIONS):
                    if not (current_day.weekday() in _not_worked_days() or current_day in VACATIONS):
                        real_duration = real_duration + 1
                        duration -= 1
                    else:
                        real_duration = real_duration + 1
        
                    current_day = self.start_date() + datetime.timedelta(days=real_duration)
        
                self.cache_end_date = self.start_date() + datetime.timedelta(days=real_duration)
                __LOG__.warning('** task "{0}" will not be finished on time : end_date is changed from {1} to {2}'.format(self.fullname, self.stop, self.cache_end_date))
                return self.cache_end_date
                    

            self.cache_end_date = real_end
            if real_end != self.stop:
                __LOG__.warning('** task "{0}" will not be finished on time : end_date is changed from {1} to {2}'.format(self.fullname, self.stop, self.cache_end_date))


                
            return self.cache_end_date

        if self.stop is None:
            current_day = self.start_date()
            real_duration = 0
            duration = self.duration   
            while duration > 1 or (current_day.weekday() in _not_worked_days() or current_day in VACATIONS):
                if not (current_day.weekday() in _not_worked_days() or current_day in VACATIONS):
                    real_duration = real_duration + 1
                    duration -= 1
                else:
                    real_duration = real_duration + 1
    
                current_day = self.start_date() + datetime.timedelta(days=real_duration)
    
            self.cache_end_date = self.start_date() + datetime.timedelta(days=real_duration)
            return self.cache_end_date

        raise(ValueError)
        return None

    def svg(self, prev_y=0, start=None, end=None, color=None, level=None):
        __LOG__.debug('** Task::svg ({0})'.format({'name':self.name, 'prev_y':prev_y, 'start':start, 'end':end, 'color':color, 'level':level}))

        if not self.display:
            __LOG__.debug('** Task::svg ({0}) display off'.format({'name':self.name}))
            return(None, 0)

        if start is None:
            start = 0

        if end is None:
            end = 9999

        # override project color if defined
        if self.color is not None:
            color = self.color

        y = prev_y * 10

        x = self.start * 10
        d = (self.duration) * 10
        
        self.drawn_y_coord = y

        svg = svgwrite.container.Group(id=self.name.replace(' ', '_'))
        svg.add(svgwrite.shapes.Rect(
                insert=((x+1)*mm, (y+1)*mm),
                size=((d-2)*mm, 8*mm),
                fill=color,
                stroke=color,
                stroke_width=2,
                opacity=0.85,
                ))
        svg.add(svgwrite.shapes.Rect(
                insert=((x+1)*mm, (y+6)*mm),
                size=(((d-2))*mm, 3*mm),
                fill="#909090",
                stroke=color,
                stroke_width=1,
                opacity=0.2,
                ))

        tx = x + 2
        svg.add(svgwrite.text.Text(self.fullname, insert=((tx)*mm, (y + 5)*mm), fill=_font_attributes()['fill'], stroke=_font_attributes()['stroke'], stroke_width=_font_attributes()['stroke_width'], font_family=_font_attributes()['font_family'], font_size=15))

        return (svg, 0)


    def svg_dependencies(self, prj):
        """
        Draws svg dependencies between task and project according to coordinates
        cached when drawing tasks

        Keyword arguments:
        prj -- Project object to check against
        """
        __LOG__.debug('** Task::svg_dependencies ({0})'.format({'name':self.name, 'prj':prj}))
        if self.depends_of is None:
            return None
        else:
            svg = svgwrite.container.Group()
            for t in self.depends_of:
                if isinstance(t, Milestone):
                    if not (t.drawn_x_end_coord is None or t.drawn_y_coord is None or self.drawn_x_begin_coord is None) and prj.is_in_project(t):
                        if t.drawn_x_end_coord < self.drawn_x_begin_coord:
                            # horizontal line
                            svg.add(svgwrite.shapes.Line(
                                    start=((t.drawn_x_end_coord + 9)*mm, (t.drawn_y_coord + 5)*mm), 
                                    end=((self.drawn_x_begin_coord)*mm, (t.drawn_y_coord + 5)*mm), 
                                    stroke='black',
                                    stroke_dasharray='5,3',
                                    ))

                            marker = svgwrite.container.Marker(insert=(5,5), size=(10,10))
                            marker.add(svgwrite.shapes.Circle((5, 5), r=5, fill='#000000', opacity=0.5, stroke_width=0))
                            svg.add(marker)
                            # vertical line
                            eline = svgwrite.shapes.Line(
                                start=((self.drawn_x_begin_coord)*mm, (t.drawn_y_coord + 5)*mm), 
                                end=((self.drawn_x_begin_coord)*mm, (self.drawn_y_coord + 5)*mm), 
                                stroke='black',
                                stroke_dasharray='5,3',
                                )
                            eline['marker-end'] = marker.get_funciri()
                            svg.add(eline)

                        else:
                            # horizontal line
                            svg.add(svgwrite.shapes.Line(
                                    start=((t.drawn_x_end_coord + 9)*mm, (t.drawn_y_coord + 5)*mm), 
                                    end=((self.drawn_x_begin_coord + 10)*mm, (t.drawn_y_coord + 5)*mm), 
                                    stroke='black',
                                    stroke_dasharray='5,3',
                                    ))
                            # vertical
                            svg.add(svgwrite.shapes.Line(
                                start=((self.drawn_x_begin_coord + 10)*mm, (t.drawn_y_coord + 5)*mm), 
                                end=((self.drawn_x_begin_coord + 10)*mm, (t.drawn_y_coord + 15)*mm), 
                                stroke='black',
                                stroke_dasharray='5,3',
                                ))
                            # horizontal line
                            svg.add(svgwrite.shapes.Line(
                                    start=((self.drawn_x_begin_coord)*mm, (t.drawn_y_coord + 15)*mm), 
                                    end=((self.drawn_x_begin_coord + 10)*mm, (t.drawn_y_coord + 15)*mm), 
                                    stroke='black',
                                    stroke_dasharray='5,3',
                                    ))
    
                            marker = svgwrite.container.Marker(insert=(5,5), size=(10,10))
                            marker.add(svgwrite.shapes.Circle((5, 5), r=5, fill='#000000', opacity=0.5, stroke_width=0))
                            svg.add(marker)
                            # vertical line
                            eline = svgwrite.shapes.Line(
                                start=((self.drawn_x_begin_coord)*mm, (t.drawn_y_coord + 15)*mm), 
                                end=((self.drawn_x_begin_coord)*mm, (self.drawn_y_coord + 5)*mm), 
                                stroke='black',
                                stroke_dasharray='5,3',
                                )
                            eline['marker-end'] = marker.get_funciri()
                            svg.add(eline)
    
                elif isinstance(t, Task):
                    if not (t.drawn_x_end_coord is None or t.drawn_y_coord is None or self.drawn_x_begin_coord is None) and prj.is_in_project(t):
                        # horizontal line
                        svg.add(svgwrite.shapes.Line(
                                start=((t.drawn_x_end_coord - 2)*mm, (t.drawn_y_coord + 5)*mm), 
                                end=((self.drawn_x_begin_coord)*mm, (t.drawn_y_coord + 5)*mm), 
                                stroke='black',
                                stroke_dasharray='5,3',
                                ))
    
                        marker = svgwrite.container.Marker(insert=(5,5), size=(10,10))
                        marker.add(svgwrite.shapes.Circle((5, 5), r=5, fill='#000000', opacity=0.5, stroke_width=0))
                        svg.add(marker)
                        # vertical line
                        eline = svgwrite.shapes.Line(
                            start=((self.drawn_x_begin_coord)*mm, (t.drawn_y_coord + 5)*mm), 
                            end=((self.drawn_x_begin_coord)*mm, (self.drawn_y_coord + 5)*mm), 
                            stroke='black',
                            stroke_dasharray='5,3',
                            )
                        eline['marker-end'] = marker.get_funciri()
                        svg.add(eline)
                    
        return svg


    def nb_elements(self):
        """
        Returns the number of task, 1 here
        """
        __LOG__.debug('** Task::nb_elements ({0})'.format({'name':self.name}))
        return 1


    def _reset_coord(self):
        """
        Reset cached elements of task
        """
        __LOG__.debug('** Task::reset_coord ({0})'.format({'name':self.name}))
        self.drawn_x_begin_coord = None
        self.drawn_x_end_coord = None
        self.drawn_y_coord = None
        self.cache_start_date = None
        self.cache_end_date = None
        return


    def is_in_project(self, task):
        """
        Return True if the given Task is itself... (lazy coding ;)
        
        Keyword arguments:
        task -- Task object 
        """
        __LOG__.debug('** Task::is_in_project ({0})'.format({'name':self.name, 'task':task}))
        if task is self:
            return True

        return False


    def get_resources(self):
        """
        Returns Resources used in the task
        """
        return self.resources



    def check_conflicts_between_task_and_resources_vacations(self):
        """
        Displays a warning for each conflict between tasks and vacation of
        resources affected to the task

        And returns a dictionnary for resource vacation conflicts
        """
        conflicts = []
        if self.get_resources() is None:
            return conflicts
        for r in self.get_resources():
            cday = self.start_date()
            while cday <= self.end_date():
                if cday.weekday() not in _not_worked_days() and not r.is_available(cday):
                    conflicts.append({'resource':r.name,'date':cday, 'task':self.name})
                    __LOG__.warning('** Caution resource "{0}" is affected on task "{2}" during vacations on day {1}'.format(r.name, cday, self.fullname))
                cday += datetime.timedelta(days=1)
        return conflicts


    def csv(self, csv=None):
        """
        Create CSV output from tasks

        Keyword arguments:
        csv -- None, dymmy object
        """
        if self.resources is not None:
            resources = ', '.join([x.fullname for x in self.resources])
        else:
            resources = ''
            
        csv_text = '"{0}";"{1}";{2};{3};{4};"{5}";\r\n'.format(
            self.state.replace('"', '\\"'),
            self.fullname.replace('"', '\\"'),
            self.start_date(),
            self.end_date(),
            self.duration,
            resources.replace('"', '\\"')
            )
        return csv_text


############################################################################


class Project(object):
    """
    Class for handling projects
    """
    def __init__(self, name="", color=None):
        """
        Initialize project with a given name and color for all tasks

        Keyword arguments:
        name -- string, name of the project
        color -- color for all tasks of the project
        """
        self.tasks = []
        self.name = name
        if color is None:
            self.color = '#FFFF90'
        else:
            self.color = color

        self.cache_nb_elements = None
        return

    def add_task(self, task):
        """
        Add a Task to the Project. Task can also be a subproject

        Keyword arguments:
        task -- Task or Project object
        """
        self.tasks.append(task)
        self.cache_nb_elements = None
        return

    def _draw_table(self, maxx, maxy):
        dwg = svgwrite.container.Group()
    
        maxx += 1
        indent = 10

        vlines = dwg.add(svgwrite.container.Group(id='vlines', stroke='lightgray'))
        for x in range(maxx):
            vlines.add(svgwrite.shapes.Line(start=((indent + x) * cm, 2*cm), end=((indent + x) * cm, (maxy+2)*cm)))
            vlines.add(svgwrite.text.Text(x,
                                            insert=(((indent + x) * 10 + 1) * mm, 19*mm),
                                            fill='black', stroke='black', stroke_width=0,
                                            font_family=_font_attributes()['font_family'], font_size=8))




        vlines.add(svgwrite.shapes.Line(start=(maxx*cm, 2*cm), end=(maxx*cm, (maxy+2)*cm)))


        hlines = dwg.add(svgwrite.container.Group(id='hlines', stroke='lightgray'))

        dwg.add(svgwrite.shapes.Line(start=((0)*cm, (2)*cm), end=((maxx)*cm, (2)*cm), stroke='black'))
        dwg.add(svgwrite.shapes.Line(start=((0)*cm, (maxy+2)*cm), end=((maxx)*cm, (maxy+2)*cm), stroke='black'))

        for y in range(2, maxy+3):
            hlines.add(svgwrite.shapes.Line(start=(0*cm, y*cm), end=(maxx*cm, y*cm)))

        return dwg


    def make_svg_for_tasks(self, filename, start=None, end=None):
        if len(self.tasks) == 0:
            __LOG__.warning('** Empty project : {0}'.format(self.name))
            return


        self._reset_coord()

        if start is None:
            start = 0
        if end is None:
            end = 9999


        if start > end:
            __LOG__.critical('start {0} > end {1}'.format(start, end))
            sys.exit(1)

        ldwg = svgwrite.container.Group()
        psvg, pheight = self.svg(prev_y=2, start=start, end=end, color = self.color)
        if psvg is not None:
            ldwg.add(psvg)

        maxx = end - start
        pheight = pheight * 10
        dwg = _my_svgwrite_drawing_wrapper(filename, debug=True)
        dwg.add(svgwrite.shapes.Rect(
                    insert=(0*cm, 0*cm),
                    size=((maxx+1)*cm, (pheight+3)*cm),
                    fill='white',
                    stroke_width=0,
                    opacity=1
                    ))

        dwg.add(self._draw_table(maxx, pheight))
        dwg.add(ldwg)
        dwg.save(width=(maxx+1)*cm, height=(pheight+3)*cm)
        return

    def start_date(self):
        """
        Returns first day of the project
        """
        if len(self.tasks) == 0:
            __LOG__.warning('** Empty project : {0}'.format(self.name))
            return datetime.date(9999, 1, 1)
        
        first = self.tasks[0].start_date()
        for t in self.tasks:
            if t.start_date() < first:
                first = t.start_date()
        return first


    def end_date(self):
        """
        Returns last day of the project
        """
        if len(self.tasks) == 0:
            __LOG__.warning('** Empty project : {0}'.format(self.name))
            return datetime.date(1970, 1, 1)

        last = self.tasks[0].end_date()
        for t in self.tasks:
            if t.end_date() > last:
                last = t.end_date()
        return last

    def svg(self, prev_y=0, start=None, end=None, color=None, level=0):
        """
        Return (SVG code, number of lines drawn) for the project. Draws all
        tasks and add project name with a purple bar on the left side.

        Keyword arguments:
        prev_y -- int, line to start to draw
        start -- datetime.date of first day to draw
        end -- datetime.date of last day to draw
        color -- string of color for drawing the project
        level -- int, indentation level of the project
        scale -- drawing scale (d: days, w: weeks, m: months, q: quaterly)
        title_align_on_left -- boolean, align task title on left
        """
        if start is None:
            start = 0
        if end is None:
            end = 9999
        if color is None or self.color is not None:
            color = self.color

        cy = prev_y + 1 * (level + 1)

        prj = svgwrite.container.Group()

        print(self.name, prev_y, cy)
        for t in self.tasks:
            trepr, theight = t.svg(prev_y, start=start, end=end, color=color, level=level+1)
            if trepr is not None:
                prj.add(trepr)
                prev_y += theight

        fprj = svgwrite.container.Group()
        prj_bar = False
        if self.name != "":
            fprj.add(svgwrite.text.Text('{0}'.format(self.name), insert=((6*level+3)*mm, ((prev_y)*10+7)*mm), fill=_font_attributes()['fill'], stroke=_font_attributes()['stroke'], stroke_width=_font_attributes()['stroke_width'], font_family=_font_attributes()['font_family'], font_size=15+3))

        # Do not display empty tasks
        if (cy - prev_y) == 0 or ((cy - prev_y) == 1 and prj_bar):
            return (None, 0)

        fprj.add(prj)
        return (fprj, 1)


    def svg_dependencies(self, prj):
        """
        Draws svg dependencies between tasks according to coordinates cached
        when drawing tasks

        Keyword arguments:
        prj -- Project object to check against
        """
        svg = svgwrite.container.Group()
        for t in self.tasks:
            trepr = t.svg_dependencies(prj)
            if trepr is not None:
                svg.add(trepr)
        return svg


    def nb_elements(self):
        """
        Returns the number of tasks included in the project or subproject
        """
        if self.cache_nb_elements is not None:
            return self.cache_nb_elements
        
        nb = 0
        for t in self.tasks:
            nb += t.nb_elements()

        self.cache_nb_elements = nb
        return nb 

    def _reset_coord(self):
        """
        Reset cached elements of all tasks and project
        """
        self.cache_nb_elements = None
        for t in self.tasks:
            t._reset_coord()
        return

    def is_in_project(self, task):
        """
        Return True if the given Task is in the project, False if not
        
        Keyword arguments:
        task -- Task object 
        """
        for t in self.tasks:
            if t.is_in_project(task):
                return True
        return False


    def get_resources(self):
        """
        Returns Resources used in the project
        """
        rlist = []
        for t in self.tasks:
            r = t.get_resources()
            if r is not None:
                rlist.append(r)

        flist = []
        for r in _flatten(rlist):
            if r not in flist:
                flist.append(r)
        return flist



    def get_tasks(self):
        """
        Returns flat list of Tasks used in the Project and subproject
        """
        tlist = []
        for t in self.tasks:
            # if it is a sub project, recurse
            if type(t) is type(self):
                st = t.get_tasks()
                tlist.append(st)
            else: # get task
                tlist.append(t)

        flist = []
        for r in _flatten(tlist):
            if r not in flist:
                flist.append(r)
        return flist


    def csv(self, csv=None):
        """
        Create CSV output from projects

        Keyword arguments:
        csv -- string, filename to save to OR file object OR None
        """
        if len(self.tasks) == 0:
            __LOG__.warning('** Empty project : {0}'.format(self.name))
            return

        if csv is not None:
            csv_text = bytes.decode(codecs.BOM_UTF8, 'utf-8')
            csv_text += '"State";"Task Name";"Start date";"End date";"Duration";"Resources";\r\n'
        else:
            csv_text = ''

        for t in self.tasks:
            c = t.csv()
            if c is not None:
                if sys.version_info[0] == 2:
                    try:
                        c = unicode(c, "utf-8")
                    except TypeError:
                        pass
                    csv_text += c
                elif sys.version_info[0] == 3:
                    csv_text += c
                else:
                    csv_text += c


        if csv is not None:
            test = False
            import io
            if sys.version_info[0] == 2:
                test = type(csv) == types.FileType or type(csv) == types.InstanceType
            elif sys.version_info[0] == 3:
                test = type(csv) == io.TextIOWrapper

            if test:
                csv.write(csv_text)
            else:
                fileobj = io.open(csv, mode='w', encoding='utf-8')
                fileobj.write(csv_text)
                fileobj.close()


        return csv_text

# MAIN -------------------
if __name__ == '__main__':
    import doctest
    # non regression test
    doctest.testmod()

else:
    init_log_to_sysout(level=logging.CRITICAL)


#<EOF>######################################################################


