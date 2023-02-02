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
indent = 60


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

        self.percent_done = percent_done
        self.drawn_x_begin_coord = None
        self.drawn_x_end_coord = None
        self.drawn_y_coord = None
        self.cache_start_date = None
        self.cache_end_date = None

        return

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
        x = (self.start + indent) * 1
        d = (self.duration) * 1
        
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

        vlines = dwg.add(svgwrite.container.Group(id='vlines', stroke='lightgray'))
        for x in range(maxx):
            vlines.add(svgwrite.shapes.Line(start=((indent + x) * mm, 2*cm), end=((indent + x) * mm, (maxy+2)*cm)))
            vlines.add(svgwrite.text.Text(x,
                                            insert=(((indent + x) + 1) * mm, 19*mm),
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
        dwg.save(width=(maxx+1)*mm, height=(pheight+3)*cm)
        return

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

        #print(self.name, prev_y, cy)
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


