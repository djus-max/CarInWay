# -*- coding: utf-8 -*-
import os
from kivy.config import Config
from kivy.app import App
from locale import getdefaultlocale
from kivy.core.window import Window
from kivy.event import EventDispatcher

from kivy.logger import Logger
from kivy.cache import Cache

from kivy.uix.image import Image 

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout

from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior  
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from kivy.properties import NumericProperty, ReferenceListProperty,\
            ListProperty, StringProperty, BooleanProperty, DictProperty,\
            ObjectProperty
from kivy.uix.bubble import Bubble
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView


# FOR SAVE
from kivy.factory import Factory
import platform
from kivy.uix.popup import Popup
import re
from kivy.clock import Clock

import threading
from functools import partial

import openrouteservice
import math
from urllib3 import *


# for save_to_write
import sqlite3
import openpyxl
from openpyxl.styles import Font
from dateutil.rrule import rrule, DAILY


# for calender
from calendar import month_name, day_abbr, Calendar, monthrange
from datetime import datetime
from datetime import date
import time

# for ProgressBar and canvas
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Ellipse, Rectangle


class BeginConfiguration():
    """
    класс создания внутренних дерикторий приложежния, насроек и базы данных для
    сохранения точек передвижения.
    """
    key='Your_key'  #! собственый ключ 
    
    def __init__(self, *args):
        self.check_platform()
        bd = SqliteMyDate()
        bd.check_table_great()
        data_dir = str(os.path.join(Calculate.APP_DIR, 'data/config.ini'))            #  TODO read before
        Config.read(data_dir)
        Cache.register('mycache')
        Calculate.config_file_set('kivy', 'log_maxfiles', '10' )
        Config.setdefaults(
            'mydata', {
                'family': '',
                'car': '',
                'carnumber': '',
                'flag': 1,
                })
        Config.write()


    def check_platform(self):
        """                         # TODO check oc.windows
        Проверка ОС.     
        При удачном импортироании  Calculate.OS_PLATFORM = 'android' , 
        иначе self.Calculate.OS_PLATFORM = 'linux'.
        Так же присваиваеться путь приложения.
        """
        try:
            from android.storage import primary_external_storage_path
            from jnius import autoclass, PythonJavaClass, java_method
            #Environment = autoclass('android.os.Environment')
            context = autoclass('android.content.Context')
            path_file = context.getExternalFilesDir(None)
            path = path_file.getAbsolutePath()
            Calculate.OS_PLATFORM = 'android'
            Calculate.APP_DIR = path

        except ImportError:
            Calculate.OS_PLATFORM = 'linux'
            Calculate.APP_DIR = os.getcwd()
            Window.size = (800, 680)


class SqliteMyDate():


    def check_table_great(self):
        ''' проверка и создание каталагов приложения в директории памяти '''
        try:
            dir_save_log = str(os.path.join(Calculate.APP_DIR, 'logs'))
            check_dir_save_log = os.path.exists(dir_save_log)
            if check_dir_save_log == False:
                os.mkdir(dir_save_log, mode=0o777)
            flag_logs = Calculate.config_file_get('kivy', 'log_dir')

            try:
                if flag_logs != dir_save_log:
                    Calculate.config_file_set('kivy', 'log_name', 'carinway_%y-%m-%d_%_.txt' )
                    Calculate.config_file_set('kivy', 'log_dir', dir_save_log )

            except:
                return 0

        except:
            return 0

        try:
            Calculate.FILE_DATA_DISTANCE = str(os.path.join(Calculate.APP_DIR, 'data/DateDistance'))
            file_check_data = os.path.exists(Calculate.FILE_DATA_DISTANCE)
            data_dir = str(os.path.join(Calculate.APP_DIR, 'data'))
            check_data_dir = os.path.exists(data_dir)
            if check_data_dir == False:
                os.mkdir(data_dir, mode=0o777)
            flag = self.great_table_distance()
            return flag

        except:
            return 0

        return 1


    def great_table_distance(self):
        '''
        Создание базы данных для хранения адресов и расчетов
        Проверка на наличие старой базы данных.
        True = создание и перезапись в таблицу. 
        '''
        con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)

        with  con:
            row = list(row for row in  con.execute("pragma table_info({table})".format(table=Calculate.MY_TABLE_ONE)).fetchall())

            if row:
                sql = '''CREATE TABLE IF NOT EXISTS {table} ("date" TEXT, "row_count" INTEGER,
                    "street" TEXT,  "lat" TEXT , "lon" TEXT, "distance" INTEGER)'''
                con.execute(sql.format(table=Calculate.MY_TABLE_TWO))
                Logger.info('Database: Database carryover "{table}" created.'.format(table=Calculate.MY_TABLE_TWO))
                args = []
                sql = 'SELECT * FROM {table}'

                for date, row_count, addr_city , addr_street, addr_housenumber, lat, lon, distance  in con.execute(sql.format(table=Calculate.MY_TABLE_ONE)):
                    arg = [date, row_count, addr_city + addr_street + addr_housenumber, lat, lon, distance]
                    args.append(arg)

                sql = 'INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?)'

                for row in args:
                    con.execute(sql.format(table=Calculate.MY_TABLE_TWO), row)

                sql = 'DROP TABLE {table}'
                con.execute(sql.format(table=Calculate.MY_TABLE_ONE))
                Logger.info('Database: Database  "{table}" delete.'.format(table=Calculate.MY_TABLE_ONE))

            elif not row:
                flag = self.check_table_for_save()

                if flag == 0:
                    sql = '''CREATE TABLE IF NOT EXISTS {table} ("date" TEXT, "row_count" INTEGER,
                        "street" TEXT,  "lat" TEXT , "lon" TEXT, "distance" INTEGER)'''
                    con.execute(sql.format(table=Calculate.MY_TABLE_TWO))
                    Logger.info('Database: Database new add "{table}" created.'.format(table=Calculate.MY_TABLE_TWO))

            con.commit()


    def check_table_for_save(self):
        con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)

        with con:
            row = list(row for row in con.execute("pragma table_info({table})".format(table=Calculate.MY_TABLE_TWO)).fetchall())

            if row:
                flag = 1
            elif not row:
                flag = 0
            return flag


def check_date(dateBegin, dateEnd):
    '''
    Проверяет наличие данных каждого дня выбранного для сохранения перед сохранением.
    Выдает ошибку "Popup" = "нету данных \n для сохранения" при отсутствии данных.
    Возращает количество дней "count" + 1 для равномерного движения кругового прогресса.
    '''
    count = 0
    con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
    cur = con.cursor()

    with con:
        for dt in rrule(DAILY, dtstart=dateBegin, until=dateEnd):
            one_day = (dt.strftime("{day}.{month}.%Y").format(day=dt.day, month=dt.month))

            sql = 'SELECT COUNT(date) from {table} where "date"=?'
            cur.execute(sql.format(table=Calculate.MY_TABLE_TWO), [one_day])
            row_count = cur.fetchone()[0]

            if row_count == 0:
                continue
            else:
                count += 1
        if count > 0:
            return True, '', count + 1
        elif count == 0:
            return False, "нету данных \n для сохранения", 0


def update_insert(date,  options):
    con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
    cur = con.cursor()
    date_now = '{day}.{monts}.{year}'.format(day=date[0], monts=date[1],year=date[2])
    sql = 'SELECT COUNT(date) from {table} where "date"=?'
    cur.execute(sql.format(table=Calculate.MY_TABLE_TWO), [date_now])
    numberOfRows = cur.fetchone()[0]

    sql_update = 'UPDATE {table} SET "street"=?, "lat" =? , "lon" =?, "distance" =? WHERE "date" = ? AND "row_count"= ? '

    for row_count in DictAdressStreet.option.keys():
        cur.execute(sql_update.format(table=Calculate.MY_TABLE_TWO), [DictAdressStreet.option[row_count]["address_street"] , 
                        DictAdressStreet.option[row_count]["lon"],
                        DictAdressStreet.option[row_count]["lat"],
                        DictAdressStreet.option[row_count]["distance"],
                        date_now, 
                        row_count ]
                    )

        if cur.rowcount == 0:
            sql_insert = 'INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ? )'
            cur.execute(sql_insert.format(table=Calculate.MY_TABLE_TWO), 
                            [date_now, 
                            row_count,
                            DictAdressStreet.option[row_count]["address_street"] , 
                            DictAdressStreet.option[row_count]["lon"],
                            DictAdressStreet.option[row_count]["lat"],
                            DictAdressStreet.option[row_count]["distance"] 
                            ]
                        )

        if row_count >= numberOfRows:
            pass
        elif row_count < numberOfRows:
            for index in range(row_count +1, numberOfRows+1):
                sql_delete = 'DELETE FROM {table} WHERE "date" = ? AND "row_count"= ?'
                cur.execute(sql_delete.format(table=Calculate.MY_TABLE_TWO), [date_now, index])
    cur.close()
    con.commit()
    con.close()

    status = "УСПЕШНО СОХРАННЕНО"
    return status


def check_table(date):
    date_now = '{day}.{monts}.{year}'.format(day=date[0], monts=date[1],year=date[2])

    options_list_date = []
    con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
    cur = con.cursor()
    sql = 'SELECT * FROM {table} WHERE "date" = ?'

    for date, row_count, addr_street,  lat , lon, distance in cur.execute(sql.format(table=Calculate.MY_TABLE_TWO), [date_now, ] ):
        row = [row_count, addr_street, lat , lon, distance]
        options_list_date.append(row)

    cur.close()
    con.close()
    return options_list_date


def check_len(day, m, y):
    date_now = '{day}.{monts}.{year}'.format(day=day[0], monts=m,year=y)
    con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
    cur = con.cursor()
    sql = 'SELECT COUNT(date) from {table} where "date"=?'
    cur.execute(sql.format(table=Calculate.MY_TABLE_TWO), [date_now])
    numberOfRows = cur.fetchone()[0]
    if  numberOfRows == 0:
        return 0
    else:
        return 1
    cur.close()
    con.close()


def delete_date(date):
    date_now = '{day}.{monts}.{year}'.format(day=date[0], monts=date[1],year=date[2])
    con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
    cur = con.cursor()
    sql = 'DELETE FROM {table} WHERE "date" = ?'
    cur.execute(sql.format(table=Calculate.MY_TABLE_TWO), [date_now,])
    cur.close()
    con.commit()
    con.close()


def total_distance_(dateBegin, dateEnd):
    total_distance = 0
    con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
    cur = con.cursor()
    for dt in rrule(DAILY, dtstart=dateBegin, until=dateEnd):
        one_day = (dt.strftime("{day}.{month}.%Y").format(day=dt.day, month=dt.month))

        sql = 'SELECT "distance" FROM {table} WHERE "date"=?'
        for distance in cur.execute(sql.format(table=Calculate.MY_TABLE_TWO), [one_day,]):
            total_distance += distance[0]

    cur.close()
    con.close()
    return total_distance


###########################################################
# KivyCalendar (X11/MIT License)
# Calendar & Date picker widgets for Kivy (http://kivy.org)
# https://bitbucket.org/xxblx/kivycalendar
# 
# Oleg Kozlov (xxblx), 2015
# https://xxblx.bitbucket.org/
###########################################################
def get_month_names():
    """ Return list with months names """

    result = []
    result = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    return result

    # If it possible get months names in system language
    try:
        with TimeEncoding("%s.%s" % getdefaultlocale('ru_RU', 'UTF-8')) as time_enc:
            for i in range(1, 13):
                result.append(month_name[i].decode(time_enc))
            
        return result
    
    except:
        return get_month_names_eng()


def get_month_names_eng():
    """ Return list with months names in english """
    
    result = []
    for i in range(1, 13):
        result.append(month_name[i])
    return result


def get_days_abbrs():
    """ Return list with days abbreviations """
    
    result = []
    result = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    # If it possible get days abbrs in system language
    try:
        with TimeEncoding("%s.%s" % getdefaultlocale()) as time_enc:
            for i in range(7):
                result.append(day_abbr[i].decode(time_enc))    
    except:
        for i in range(7):
            result.append(day_abbr[i])
    
    return result


def calc_quarter(y, m):
    """ Calculate previous and next month """
    
    # Previous / Next month's year number and month number
    prev_y = y
    prev_m = m - 1
    next_y = y
    next_m = m + 1    
    
    if m == 1:
        prev_m = 12
        prev_y = y - 1
    elif m == 12:
        next_m = 1
        next_y = y + 1
        
    return [(prev_y, prev_m), (y, m), (next_y, next_m)]


def get_month(y, m):
    """ 
    Return list of month's weeks, which day 
    is a turple (<month day number>, <weekday number>) 
    """
    
    cal = Calendar()
    # РАСЧИТЫВАЕТ ПРИНАДЛЕЖНОСТЬ ДНЕЙ НЕДЕЛИ К МЕСЯЦУ НА ПРЕД ТЕКУЩИЙ И СЛЕД МЕСЯЦ
    month = cal.monthdays2calendar(y, m)
    
    # Add additional num to every day which mark from 
    # this or from other day that day numer

    # ################## НАЧАЛО ПЕРЕБОРА 
    for week in range(len(month)):
        for day in range(len(month[week])):
            _day = month[week][day]
            if _day[0] == 0:
                this = 0
                flag = 0
            else: 
                flag = check_len(_day, m, y)
                this = 1

            _day = (_day[0], _day[1], this, flag)

            month[week][day] = _day


    # Days numbers of days from preious and next monthes
    # marked as 0 (zero), replace it with correct numbers
    # If month include 4 weeks it hasn't any zero
    if len(month) == 4:
        return month        
    
    quater = calc_quarter(y, m)
    
    # Zeros in first week    
    fcount = 0
    for i in month[0]:
        if i[0] == 0:
            fcount += 1
    
    # Zeros in last week
    lcount = 0
    for i in month[-1]:
        if i[0] == 0:
            lcount += 1
            
    if fcount:
        # Last day of prev month
        n = monthrange(quater[0][0], quater[0][1])[1]
        
        for i in range(fcount):
            month[0][i] = (n - (fcount - 1 - i), i, 0)
            
    if lcount:
        # First day of next month
        n = 1
        
        for i in range(lcount):
            month[-1][-lcount + i] = (n + i, 7 - lcount + i, 0)
    
    return month


def get_quarter(y, m):
    """ Get quarter where m is a middle month """
    
    result = []
    quarter = calc_quarter(y, m)
    for i in quarter:
        result.append(get_month(i[0], i[1]))
    
    return result


def today_date_list():
    """ Return list with today date """
    
    return [datetime.now().day, datetime.now().month, datetime.now().year]


def today_date():
    """ Return today date dd.mm.yyyy like 28.02.2015 """
    return datetime.now().strftime("%d-%m-%Y")


#  #############################################################
Builder.load_string("""
<ArrowButton>:
    background_normal: ""
    background_down: ""
    background_color: 1, 1, 1, 0
    size_hint: .1, .1
<MonthYearLabel>:
    pos_hint: {"top": 1, "center_x": .5}
    size_hint: None, 0.1
    halign: "center"
<MonthsManager>:
    pos_hint: {"top": .9}
    size_hint: 1, .9
<ButtonsGrid>:
    cols: 7
    rows: 7
    size_hint: 1, 1
    pos_hint: {"top": 1}
<DayAbbrLabel>:
    text_size: self.size[0], None
    halign: "center"
<DayAbbrWeekendLabel>:
    color: 1, 0, 0, 1
<DayButton>:
    group: "day_num"
<DayNumWeekendButton>:
    #background_color: 1, 0, 0, 1
""")    
###########################################################


# ####################################################
class DatePicker(TextInput):
    """ 
    Date picker is a textinput, if it focused shows popup with calendar
    which allows you to define the popup dimensions using pHint_x, pHint_y, 
    and the pHint lists, for example in kv:
    DatePicker:
        pHint: 0.7,0.4 
    would result in a size_hint of 0.7,0.4 being used to create the popup
    """
    pHint_x = NumericProperty(0.8)
    pHint_y = NumericProperty(0.6)
    pHint = ReferenceListProperty(pHint_x ,pHint_y)


    def __init__(self, touch_switch=False, *args, **kwargs):
        super(DatePicker, self).__init__(*args, **kwargs)
        
        self.touch_switch = touch_switch
        self.init_ui() 

        MyClass.date_begin = today_date_list()
        MyClass.date_end = today_date_list()

    
    def init_ui(self):
        self.text = today_date()
        # Calendar
        self.cal = CalendarWidget(as_popup=True, 
                                touch_switch=self.touch_switch, flag=False)
        # Popup
        self.popup = Popup(content=self.cal, background_color = (0,0,0,0.9), background = './data/img/f.png',
                                separator_height = 0, on_dismiss=self.update_value,  title="")
        self.cal.parent_popup = self.popup
        self.bind(focus=self.show_popup)


    def show_popup(self, isnt, val):
        """ 
        Open popup if textinput focused, 
        and regardless update the popup size_hint 
        """
        self.popup.size_hint=self.pHint        
        if val:
            # Automatically dismiss the keyboard 
            # that results from the textInput 
            Window.release_all_keyboards()
            self.popup.open()

    
    def update_value(self, inst):
        """ Update textinput value on popup close """
            
        self.text = "%s-%s-%s" % tuple(self.cal.active_date)
        self.focus = False
        self.check_date( tuple(self.cal.active_date))


    def check_date(self, value):  
        
        if self.parent.parent.parent.parent.parent.ids.date_begin == self:
            MyClass.date_begin = self.cal.active_date

        elif self.parent.parent.parent.parent.parent.ids.date_end == self:
            MyClass.date_end = self.cal.active_date

        self.dateBegin = date(MyClass.date_begin[2], MyClass.date_begin[1], MyClass.date_begin[0])
        self.dateEnd = date(MyClass.date_end[2], MyClass.date_end[1], MyClass.date_end[0])
        
        if self.dateBegin <= self.dateEnd:
            flag =  SqliteMyDate().check_table_for_save()
            if flag == 1:
                self.total_distance_write()
            else:
                status = 'Извините, но данные не обнаруженны. Перезагрузите приложение.'
                self.show_status_popup(status)
                return


    def total_distance_write(self):
        total_distance = total_distance_(self.dateBegin, self.dateEnd)
        self.parent.parent.parent.parent.parent.ids.total.text = str(total_distance) + 'км'


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0,
                                background =  './data/img/f.png', opacity = 1, size_hint=(0.7, 0.2))
        self._popup.open()
            


class MyClass(EventDispatcher):
    index_rows = NumericProperty(0)
    date = today_date()
    date_begin = ObjectProperty(0) 
    date_end = ObjectProperty(0)
    canvas_color_text = ListProperty([1,1,1,0.5])
    count_date = NumericProperty(0)



###########################################################
# KivyCalendar (X11/MIT License)
# Calendar & Date picker widgets for Kivy (http://kivy.org)
# https://bitbucket.org/xxblx/kivycalendar
# 
# Oleg Kozlov (xxblx), 2015
# https://xxblx.bitbucket.org/
###########################################################

class Calendar1(BoxLayout):
    pass


class CalendarWidget(RelativeLayout):
    """ Basic calendar widget """
    def __init__(self, as_popup=False, touch_switch=False, flag=True,  *args, **kwargs):
        super(CalendarWidget, self).__init__(*args, **kwargs)
        self.flag = flag
        self.as_popup = as_popup
        self.touch_switch = touch_switch
        self.prepare_data()     
        self.init_ui()
        
    def init_ui(self):
        self.left_arrow = ArrowButton(text="<", on_press=self.go_prev,
                                      pos_hint={"top": 1, "left": 0})
        
        self.right_arrow = ArrowButton(text=">", on_press=self.go_next,
                                       pos_hint={"top": 1, "right": 1})
        self.add_widget(self.left_arrow)        
        self.add_widget(self.right_arrow)
        
        # Title        
        self.title_label = MonthYearLabel(text=self.title)
        self.add_widget(self.title_label)
        
        # ScreenManager
        self.sm = MonthsManager()
        self.add_widget(self.sm)
        
        self.create_month_scr(self.quarter[1], toogle_today=True) 
    
    def create_month_scr(self, month, toogle_today=False):
        """ Screen with calendar for one month """ 
        scr = Screen()
        m = self.month_names_eng[self.active_date[1] - 1]
        scr.name = "%s-%s" % (m, self.active_date[2])  # like march-2015

        # Grid for days
        grid_layout = ButtonsGrid()
        scr.add_widget(grid_layout)
        
        # Days abbrs 
        for i in range(7):
            if i >= 5:  # weekends
                l = DayAbbrWeekendLabel(text=self.days_abrs[i])
            else:  # work days
                l = DayAbbrLabel(text=self.days_abrs[i])
            
            grid_layout.add_widget(l)
            
        # Buttons with days numbers
        for week in month:
            for day in week:
                # перебирает список всех кнопок и устанавливает значение 

                if day[1] >= 5:  # weekends
                    try:
                        if day[3] == 1:
                            tbtn = DayNumWeekendButton(text=str(day[0]),
                                                        background_color= ([0.16, 0.6, 0, 1]))
                        else:
                            tbtn = DayNumWeekendButton(text=str(day[0]),
                                                        background_color= [1, 0, 1, 1])
                    
                    except IndexError:
                        tbtn = DayNumWeekendButton(text=str(day[0]),
                                                    background_color= [1, 0, 1, 1])
                                                
                else:  # work days
                    try:
                        if day[3] == 1:
                            tbtn = DayNumButton(text=str(day[0]),
                                                    background_color= [0.1, 0.6, 0, 1])
                            pass
                        
                        else:
                            tbtn = DayNumButton(text=str(day[0]),
                                                    background_color= [0, 1, 1, 1])
                    except IndexError:
                        tbtn = DayNumButton(text=str(day[0]),
                                                    background_color= [0, 1, 1, 1])
                
                try:
                    if day[3] == 1:
                        if self.flag == True:
                            tbtn.bind(on_press=self.check_time, on_release=self.get_btn_value)
                        else:
                            tbtn.bind(on_release=self.get_value)
                    else:
                        if self.flag == True:
                            tbtn.bind(on_release=self.move_widget)
                        else:
                            tbtn.bind(on_release=self.get_value)
                except IndexError:
                    pass
                
                if toogle_today:
                    # Down today button
                    if day[0] == self.active_date[0] and day[2] == 1:
                        tbtn.state = "down"
                # Disable buttons with days from other months
                if day[2] == 0:
                    tbtn.disabled = True
                
                grid_layout.add_widget(tbtn)

        self.sm.add_widget(scr)
        

    def get_value(self, inst):
        """ Get day value from pressed button """
        
        self.active_date[0] = int(inst.text)
                
        if self.as_popup:
            self.parent_popup.dismiss()


    def move_widget(self, inst):
        self.active_date[0] = int(inst.text)
        self.parent.parent.parent.parent.add_screen_manager(self.active_date)


    def check_time(self, inst):
        self.start = time.time()        


    def prepare_data(self):
        """ Prepare data for showing on widget loading """
    
        # Get days abbrs and month names lists 
        self.month_names = get_month_names()
        self.month_names_eng = get_month_names_eng()
        self.days_abrs = get_days_abbrs()    
        
        # Today date
        self.active_date = today_date_list()
        # Set title
        self.title = "%s - %s" % (self.month_names[self.active_date[1] - 1], 
                                  self.active_date[2])
                
        # Quarter where current month in the self.quarter[1]
        self.get_quarter()
    
    def get_quarter(self):
        """ Get caledar and months/years nums for quarter """
        
        self.quarter_nums = calc_quarter(self.active_date[2], 
                                                  self.active_date[1])
        self.quarter = get_quarter(self.active_date[2], 
                                            self.active_date[1])
    
    def get_btn_value(self, inst):                                        
        """ Get day value from pressed button """
        self.active_date[0] = int(inst.text)

        finish = time.time()            
        result = finish - self.start
        if result > 0.6 :
            self.drop_down(inst)
        else:
            self.parent.parent.parent.parent.add_screen_manager(self.active_date)

        
    def drop_down(self, inst):
        self.dropdown = DropDownn()

        but = Button(text='удалить',                         
                    size_hint= (None, None),
                    height = '30sp',
                    background_color = [1, 0, 0, 1],
                    font_size='10sp',
                    on_release=lambda but: self.on_select(but, inst))

        self.dropdown.add_widget(but)
        self.dropdown.open(inst)


    def on_select(self, but , instance ):
        self.but_select = instance
        flag = SqliteMyDate().check_table_for_save()
        if flag == 1:
            delete_date(self.active_date)
            self.but_select.background_color = self.but_select.color
            self.dropdown.dismiss()
            return
        else:
            status = 'Извините, но данные не обнаруженны. Перезагрузите приложение.'
            self.show_status_popup(status)
            return


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0,
                                background =  './data/img/f.png', opacity = 0, size_hint=(0.7, 0.2))
        self._popup.open()


    def go_prev(self, inst):
        """ Go to screen with previous month """        

        # Change active date
        self.active_date = [self.active_date[0], self.quarter_nums[0][1], 
                            self.quarter_nums[0][0]]

        # Name of prev screen
        n = self.quarter_nums[0][1] - 1
        prev_scr_name = "%s-%s" % (self.month_names_eng[n], 
                                   self.quarter_nums[0][0])
        
        # If it's doen't exitst, create it
        if not self.sm.has_screen(prev_scr_name):
            self.create_month_scr(self.quarter[0])
            
        self.sm.current = prev_scr_name
        self.sm.transition.direction = "right"
        
        self.get_quarter()
        self.title = "%s - %s" % (self.month_names[self.active_date[1] - 1], 
                                  self.active_date[2])
        
        self.title_label.text = self.title
    
    def go_next(self, inst):
        """ Go to screen with next month """
        
         # Change active date
        self.active_date = [self.active_date[0], self.quarter_nums[2][1], 
                            self.quarter_nums[2][0]]

        # Name of prev screen
        n = self.quarter_nums[2][1] - 1
        next_scr_name = "%s-%s" % (self.month_names_eng[n], 
                                   self.quarter_nums[2][0])
        
        # If it's doen't exitst, create it
        if not self.sm.has_screen(next_scr_name):
            self.create_month_scr(self.quarter[2])
            
        self.sm.current = next_scr_name
        self.sm.transition.direction = "left"
        
        self.get_quarter()
        self.title = "%s - %s" % (self.month_names[self.active_date[1] - 1], 
                                  self.active_date[2])
        
        self.title_label.text = self.title
        
    def on_touch_move(self, touch):
        """ Switch months pages by touch move """
                
        if self.touch_switch:
            # Left - prev
            if touch.dpos[0] < -30:
                self.go_prev(None)
            # Right - next
            elif touch.dpos[0] > 30:
                self.go_next(None)


class DropDownn(DropDown):
    auto_width= BooleanProperty(True)


class SaveButton(ButtonBehavior, Image):  
        pass

class CancelButton(ButtonBehavior, Image):  
        pass


class ArrowButton(Button):
    pass

class MonthYearLabel(Label):
    pass

class MonthsManager(ScreenManager):
    pass

class ButtonsGrid(GridLayout):
    pass

class DayAbbrLabel(Label):
    pass

class DayAbbrWeekendLabel(DayAbbrLabel):
    pass

class DayButton(ToggleButton):
    pass

class DayNumButton(DayButton):
    color = ListProperty([0, 1, 1, 1])
    pass
    

class DayNumWeekendButton(DayButton):
    color = ListProperty([1, 0, 1, 1])
    pass


class HomeBackButton(ButtonBehavior, Image):
    pass


class BackButton(ButtonBehavior, Image):  
    pass


class UpdateButton(ButtonBehavior, Image):  
    pass 


class SaveDateButton(ButtonBehavior, Image):  
    pass 


class AddButton(ButtonBehavior, Image):  
    pass 

class DeletetButton(ButtonBehavior, Image):  
    pass 


class NavigationButton(ButtonBehavior, Image):
    pass 


class HeaderWidget(BoxLayout):
    pass


class FooterWidget(BoxLayout):
    pass


class Footer(BoxLayout):
    pass

class FirstScreenFooter(BoxLayout):
    pass


class widget_one(BoxLayout):
    pass


class ScrollView(ScrollView):
    pass


class BoxLayout_(BoxLayout):
    pass



class ValidateLabel(Bubble):
    validated = False


class ErorrPopup(BoxLayout):
    pass

class GoodPopup(BoxLayout):
    pass


class MyTextInput(TextInput):
    canvas_color_radius = ListProperty([0, 0, 1, 0.5])
    canvas_color_text = ListProperty([1,1,1,0.5])


class WidgetBeginOne(BoxLayout):
    canvas_background_color = ListProperty()
    def __init__(self, **kwargs):
        super(WidgetBeginOne, self).__init__(**kwargs)
        self.canvas_background_color = (0, 0, 1, 0)


_grid_kv = '''
GridLayout:
    size_hint_y: None
    height: self.minimum_size[1]
    cols: 1
'''

class DropDown(ScrollView):
    auto_width = BooleanProperty(True)
    max_height = NumericProperty(None, allownone=True)
    dismiss_on_select = BooleanProperty(True)
    auto_dismiss = BooleanProperty(True)
    min_state_time = NumericProperty(0)
    attach_to = ObjectProperty(allownone=True)
    container = ObjectProperty()
    _touch_started_inside = None
    __events__ = ('on_select', 'on_dismiss')


    def __init__(self, **kwargs):
        super(DropDown, self).__init__(**kwargs)
        
        self._win = None
            
        if 'container' not in kwargs:
            c = self.container = Builder.load_string(_grid_kv)
        else:
            c = None
        if 'do_scroll_x' not in kwargs:
            self.do_scroll_x = False
        
        if 'size_hint' not in kwargs:
            if 'size_hint_x' not in kwargs:
                self.size_hint_x = None
            if 'size_hint_y' not in kwargs:
                self.size_hint_y = None

        if c is not None:
            super(DropDown, self).add_widget(c)
            self.on_container(self, c)
        Window.bind(
            on_key_down=self.on_key_down,
            size=self._reposition)
        self.fbind('size', self._reposition)


    def on_key_down(self, instance, key, scancode, codepoint, modifiers):
        if key == 13 and self.get_parent_window():     # 27
            self.dismiss()
            return True

    def on_container(self, instance, value):
        if value is not None:
            self.container.bind(minimum_size=self._reposition)

    def open(self, widget):
        '''Open the dropdown list and attach it to a specific widget.
        Depending on the position of the widget within the window and
        the height of the dropdown, the dropdown might be above or below
        that widget.
        '''
        # ensure we are not already attached
        if self.attach_to is not None:
            self.dismiss()

        # we will attach ourself to the main window, so ensure the
        # widget we are looking for have a window
        self._win = widget.get_parent_window()
        if self._win is None:
            raise DropDownException(
                'Cannot open a dropdown list on a hidden widget')

        self.attach_to = widget
        widget.bind(pos=self._reposition, size=self._reposition)
        self._reposition()

        # attach ourself to the main window
        try:
            self._win.add_widget(self)
        except:
            return


    def dismiss(self, *largs):
        '''Remove the dropdown widget from the window and detach it from
        the attached widget.
        '''
        try:
            Clock.schedule_once(self._real_dismiss, self.min_state_time)
        except:
            pass


    def _real_dismiss(self, *largs):
        if self.parent:
            self.parent.remove_widget(self)
        if self.attach_to:
            self.attach_to.unbind(pos=self._reposition, size=self._reposition)
            self.attach_to = None
        self.dispatch('on_dismiss')

    def on_dismiss(self):
        pass

    def select(self, data):
        '''Call this method to trigger the `on_select` event with the `data`
        selection. The `data` can be anything you want.
        '''
        self.dispatch('on_select', data)
        if self.dismiss_on_select:
            self.dismiss()


    def on_select(self, data):
        self.dismiss()
        pass

    def add_widget(self, *largs):
        if self.container:
            return self.container.add_widget(*largs)
        return super(DropDown, self).add_widget(*largs)


    def remove_widget(self, *largs):
        if self.container:
            return self.container.remove_widget(*largs)
        return super(DropDown, self).remove_widget(*largs)


    def clear_widgets(self):
        if self.container:
            return self.container.clear_widgets()
        return super(DropDown, self).clear_widgets()


    def on_touch_down(self, touch):
        self._touch_started_inside = self.collide_point(*touch.pos)
        if not self.auto_dismiss or self._touch_started_inside:
            super(DropDown, self).on_touch_down(touch)
        return True


    def on_touch_move(self, touch):
        if not self.auto_dismiss or self._touch_started_inside:
            super(DropDown, self).on_touch_move(touch)
        return True


    def on_touch_up(self, touch):
        # Explicitly test for False as None occurs when shown by on_touch_down
        if self.auto_dismiss and self._touch_started_inside is False:
            self.dismiss()
        else:
            super(DropDown, self).on_touch_up(touch)
        self._touch_started_inside = None
        return True


    def _reposition(self, *largs):
        # calculate the coordinate of the attached widget in the window
        # coordinate system
        win = self._win
        widget = self.attach_to
        if not widget or not win:
            return
        wx, wy = widget.to_window(*widget.pos)
        wright, wtop = widget.to_window(widget.right, widget.top)


        # set width and x
        if self.auto_width:
            self.width = wright - wx

        # ensure the dropdown list doesn't get out on the X axis, with a
        # preference to 0 in case the list is too wide.
        x = wx
        if x + self.width > win.width:
            x = win.width - self.width
        if x < 0:
            x = 0
        self.x = x

        # determine if we display the dropdown upper or lower to the widget
        if self.max_height is not None:
            height = min(self.max_height, self.container.minimum_height)

        else:
            height = self.container.minimum_height

        part_window = Window.height / 2.5

        h_bottom = (wy - part_window) - height
        h_top = win.height - (wtop + height)
        if h_bottom > 0:  
            self.top = wy               # позиция drop , если он наверху
            self.height = height

        elif h_top > 0:
            self.y =  wtop               # позиция drop , если он внизу
            self.height = height

        else:
            # none of both top/bottom have enough place to display the
            # widget at the current size. Take the best side, and fit to
            # it.
            if h_top < h_bottom:                    #  направление drop вниз, если виджет наверху 
                self.top = wy
                self.height = wy - (Window.height / 2.5)

            else:               # левй край
                self.y = wtop 
                self.height = win.height - wtop



#  ОСНОВНЫЕ ВИДЖЕТЫ
class widget_two(BoxLayout):
    canvas_color_text_valid = ListProperty([8/255, 88/255, 13/255, 1])
    canvas_color_text_invalid = ListProperty([1, 0, 0, 1])
    canvas_color_text_introduced = ListProperty([1,1,1,1])
    canvas_color_radius_active = ListProperty([0, 1, 1, 1])
    canvas_color_radius_deactive = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_address_street = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_active = ListProperty([0, 1, 1, 1])
    canvas_color_holst_deative = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_number_house = ListProperty([0, 0, 1, 0.5])
    button_info = DictProperty()
    flag = BooleanProperty(False)
    check_len_value = NumericProperty(0)
    check_len_address = NumericProperty(1)


    def __init__(self, **kw):
        super(widget_two, self).__init__(**kw)
        self.dropdown=DropDown()
        self.DictAdressStreet = DictAdressStreet()


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0, 
                                background =  './data/img/f.png', opacity = 1, size_hint=(0.3, 0.1))
        self._popup.open()
    

    def focus(self, instance, value):
        if instance.focus == True:
            self.con = sqlite3.Connection(Calculate.FILE_DATA_ASTRAKHAN)          

            instance.canvas_color_radius = self.canvas_color_radius_active
            self.canvas_color_holst_address_street = self.canvas_color_holst_active

        
        elif len(value) == 0:
            instance.canvas_color_text = (1,1,1,0.5)
            instance.canvas_color_radius = self.canvas_color_radius_deactive
            self.canvas_color_holst_address_street = self.canvas_color_holst_deative
            self.canvas_color_holst_number_house = self.canvas_color_holst_deative

        else:
            instance.canvas_color_radius = self.canvas_color_radius_deactive
            self.canvas_color_holst_address_street = self.canvas_color_holst_deative

        if instance.focus == False:
            self.check_len_value = 0
            self.check_len_address = 1
            self.con.close()


    def validate(self, instance, value):
        if self.check_len_value < len(value):
            if instance.focus == True and self.flag == False:
                self.check_len_value = len(value)

                if len(value) > 30:      # TODO
                    instance.text = value[:-1]
                    return
                
                else:
                    if value[0] == ' ':
                        instance.text = value.lstrip()
                        return
                    else:
                        status = True
                        status = re.search(r'[^0-9А-Яа-яЁё\s-]', value) 
                        if   status :
                            self.dropdown.dismiss()
                            instance.canvas_color_text = self.canvas_color_text_invalid
                            return

                        elif not status:
                            instance.canvas_color_text = self.canvas_color_text_valid

                            if len(value) > 0 and (self.check_len_address > 0):
                                self.flag = True
                                address  = self.sourse_address(value)
                                self.check_len_address = len((address))
                                self.drop_down( instance, address )

                            else:
                                self.flag = False
                                self.dropdown.dismiss()
        else:
            self.check_len_value = len(value)
            self.check_len_address = 1
            self.dropdown.dismiss()
            return
        

    def drop_down( self, instance, items_address):
        self.button_info.clear()
        self.dropdown.dismiss()
        self.dropdown = DropDown()

        for items in items_address:                 
            item = items[0]
            but = Button(text=item,                       
                        background_color = [0, 1, 1, 1],
                        size_hint_y=None,
                        text_size= instance.size, 
                        halign= 'center',
                        valign= 'middle',
                        height='30sp',
                        font_size='10sp',
                        on_release=lambda but: self.on_select(but, but.text, instance ))
            self.button_info.update({
                                        but : items
                                    })

            self.dropdown.add_widget(but)

        self.dropdown.open(instance)
        self.flag = False


    def on_select(self, but, value, instance):
        for key, val in self.button_info.items():
            if but == key:
                items_address = val
                break
        
        for key in self.DictAdressStreet.option.keys():            
            if self == self.DictAdressStreet.option[key]['widget']:
                self.DictAdressStreet.install(row=key, address_street=items_address[0], 
                                            address_street_bool=True, lon=items_address[1], 
                                            lat=items_address[2])

        self.check_len_value = 0
        self.check_len_address = 1
        instance.multiline = True
        instance.is_focusable = False
        instance.text = value
        instance.canvas_color_text = self.canvas_color_text_introduced
        self.dropdown.dismiss()


    def change_row(self, instance):
        for key in self.DictAdressStreet.option.keys():            
            if self == self.DictAdressStreet.option[key]['widget']:
                self.DictAdressStreet.update(row=key, widget=self)

        self.ids.address_street.is_focusable = True
        self.ids.address_street.text =  ''
        self.ids.distance.text = ''
        self.ids.address_street.canvas_color_text = (1,1,1,0.5)
        self.check_len_value = 0
        self.check_len_address = 1


    def sourse_address(self, address):                  # TODO
        cur = self.con.cursor()
        address = str(address)
        addd = address.split(' ')
        city_street = []

        sql = 'SELECT DISTINCT  "street", "lat", "lon" FROM address WHERE '
        where = []
        args = []
        
        # Собираем все условия LIKE, которые потом соединим через OR/AND
        for award in addd:
            where.append('"street" LIKE ? ')
            # Слова передаём отдельно, чтобы защититься от SQL-инъекции
            args.append('%' + award + '%')
            
        # Собираем SQL-запрос до конца
        sql += '  AND '.join(where)  # или AND
        sql += ''.join('ORDER BY "street" ASC LIMIT 8')
        for street , lat, lon  in cur.execute(sql, args):
            street_lon_lat = (street, lon, lat)
            city_street.append(street_lon_lat)
            
        cur.close()
        return city_street


class DictAdressStreet():
    option = {}


    def install(self, row, **kwargs):
        try:
            self.option[row]
        except KeyError:
            self.option[row] = {}
        
        for key , val in kwargs.items():
            self.option[row][key] = val


    def update(self, row, widget):
        self.option.update({
                        row : {
                            'widget': widget,}
                            })

    
    def delete_row(self, row_widget, row):
        row_widget.boxLayout_.remove_widget(self.option[row]['widget'])
        del self.option[row]


class widget_three(BoxLayout):
    canvas_color_text_valid = ListProperty([0.16,0.58,0,1])
    canvas_color_text_invalid = ListProperty([1, 0, 0, 1])
    canvas_color_text_introduced = ListProperty([1,1,1,1])
    canvas_color_radius_active = ListProperty([0, 1, 1, 1])
    canvas_color_radius_deactive = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_family = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_active = ListProperty([0, 1, 1, 1])
    canvas_color_holst_deative = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_car = ListProperty([0, 0, 1, 0.5])
    canvas_color_holst_number_car = ListProperty([0, 0, 1, 0.5])


    def focus(self, instance, value):
        if instance.focus == True:
            if self.ids.family == instance:
                instance.canvas_color_text = (0,0,0)
                instance.canvas_color_radius = self.canvas_color_radius_active
                self.canvas_color_holst_family = self.canvas_color_holst_active

            elif self.ids.car == instance:
                instance.canvas_color_text = (0,0,0)
                instance.canvas_color_radius = self.canvas_color_radius_active
                self.canvas_color_holst_car = self.canvas_color_holst_active

            elif self.ids.number_car == instance:
                instance.canvas_color_text = (0,0,0)
                instance.canvas_color_radius = self.canvas_color_radius_active
                self.canvas_color_holst_number_car = self.canvas_color_holst_active

        elif len(value) == 0:
            instance.canvas_color_text = (1,1,1,0.5)
            self.canvas_color_holst_family = self.canvas_color_holst_deative
            self.canvas_color_holst_car = self.canvas_color_holst_deative
            self.canvas_color_holst_number_car = self.canvas_color_holst_deative
            instance.canvas_color_radius = self.canvas_color_radius_deactive

            if self.ids.family == instance:
                Calculate.config_file_set('mydata', 'family', value)
                
            elif self.ids.car == instance:
                Calculate.config_file_set('mydata', 'car', value)

            elif self.ids.number_car == instance:
                Calculate.config_file_set('mydata', 'carnumber', value)

        else:
            instance.canvas_color_text = self.canvas_color_text_introduced
            instance.canvas_color_radius = self.canvas_color_radius_deactive
            self.canvas_color_holst_family = self.canvas_color_holst_deative
            self.canvas_color_holst_car = self.canvas_color_holst_deative
            self.canvas_color_holst_number_car = self.canvas_color_holst_deative

            if self.ids.family == instance:
                Calculate.config_file_set('mydata', 'family', value)
                
            elif self.ids.car == instance:
                Calculate.config_file_set('mydata', 'car', value)

            elif self.ids.number_car == instance:
                Calculate.config_file_set('mydata', 'carnumber', value)

    def validate(self, instance, value):
        if len(value) > 18:
            instance.text = value[:-1]
            return




#  SCREEN 
class FirstScreenOne(Screen):
    count = 0
    canvas_background_color = (0, 0, 1, 1)
    def __init__(self, **kwargs):
        super(FirstScreenOne, self).__init__(**kwargs)
        self.widget  = WidgetBeginOne()
        self.widget.ids.home_page.text = 'Добро пожаловать\nв тестовую демо-версию приложения по подсчету расстояний и занесением в путевые листы'

        self.add_widget(self.widget)


    def add_widget_one(self, instance):
        if self.count == 0:
            self.count += 1
            #self.ids.delete_first_screen.opacity = 0
            self.widget.ids.home_page.text = 'Даннное приложение\nвключают базу данных более чем 60000 адресов Астраханской области, более чем 3000 улиц, включая около 300 сел и поселков'

        elif self.count == 1:
            self.count += 1
            self.widget.ids.home_page.text = 'Перед использованием убедитесь в наличии интеренета.'
            self.widget.ids.delete_first_screen.opacity = 1
            self.widget.ids.delete_first_screen.disabled =False
            self.widget.canvas_background_color = (0, 0, 1, 1)
            
        elif self.count == 2:
            if self.widget.ids.delete_first_screen == instance:
                Calculate.config_file_set('mydata', 'flag', 0)
        
            self.parent.first_screen_two()


class FirstScreenTwo(Screen):
    canvas_background_color = (0, 0, 1, 1)

    def __init__(self, **kwargs):
        super(FirstScreenTwo, self).__init__(**kwargs)

        self.widget  = WidgetBeginOne()
        self.widget.ids.center_box.size_hint = (1,2)
        self.widget.ids.home_page.text = ('Данные приложения \n будут храниться по пути: '
                                        '\n{dir}' 
                                        '\n\n Там Вы сможете найти свои сохраненные путевые листы,'
                                        ' а также логи, которые в случае краха приложения вы всегда можете'
                                        ' отправить вместе со своими пожеланиями и отзывами'
                                        ' на адрес электронной почты:'
                                        '\n\ncarinway.djus@gmail.com' .format(dir=Calculate.APP_DIR))

        self.widget.ids.after_button.size_hint = (0.4,0.8)
        self.add_widget(self.widget)


    def add_widget_one(self, instance):
        Clock.schedule_once(partial(self.parent.first_screen))



class FirstScreen(Screen):
    
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)
        self.headerWidget = HeaderWidget()
        self.headerWidget.size = (Window.width, Window.height/12)
        self.headerWidget.pos = (0, Window.size[1] - self.headerWidget.height)
        self.headerWidget.ids.back_button.opacity = 0       
        self.headerWidget.ids.back_button.disabled = True
        self.add_widget(self.headerWidget)

        self.FirstScreenFooter = FirstScreenFooter()
        self.FirstScreenFooter.size = (Window.width, '15sp')
        self.FirstScreenFooter.pos = (0, 0)
        self.add_widget(self.FirstScreenFooter)

        self.calendarWidget = Calendar1()
        self.calendarWidget.size = (Window.width, Window.height - self.headerWidget.height )
        self.calendarWidget.pos = (0, self.FirstScreenFooter.height)
        self.calendarWidget.padding = ('5sp', '5sp', '5sp', '3sp')
        self.add_widget(self.calendarWidget)


class SecondScreen(Screen):
    count = MyClass()
    row = count.index_rows                                  
    part = 15  

    def __init__(self, date, **kwargs):
        super(SecondScreen, self).__init__(**kwargs)
        self.date = date
        self.DictAdressStreet = DictAdressStreet()
        self.DictAdressStreet.option.clear()
        self.headerWidget = HeaderWidget()
        self.headerWidget.size = (Window.width, Window.height/12)
        self.headerWidget.pos = (0, Window.height - self.headerWidget.height)
        self.add_widget(self.headerWidget)
        self.pass_widget = self.headerWidget

        # инициализация и добавление первой строки
        self.widget_one  = widget_one()
        self.widget_one.size = (Window.width, Window.height/12)
        self.widget_one.pos = (0, self.pass_widget.pos[1] - self.widget_one.height)
        self.widget_one.ids.now_data.text = '%s  %s' % (date[0],  self.date_transformation(self.date))        # TODO
        self.add_widget(self.widget_one)
        self.pass_widget = self.widget_one

        self.footer = Footer()
        self.footer.size = (Window.width, Window.height/25)
        self.footer.pos = (0, 0)
        self.add_widget(self.footer)

        self.FooterWidget = FooterWidget()
        self.FooterWidget.size = (Window.width, Window.height/self.part)
        self.FooterWidget.pos = (0, self.footer.height )
        self.add_widget(self.FooterWidget)

        self.scrollview = ScrollView(bar_width = 8, size_hint_y= None)
        self.scrollview.pos = (0, self.FooterWidget.pos[1] + self.FooterWidget.height * 1.5)
        self.scrollview.size = (Window.width,  Window.height - self.scrollview.pos[1] - self.widget_one.height - self.headerWidget.height)

        self.add_widget(self.scrollview)

        self.boxLayout_ = BoxLayout_(orientation = 'vertical', size_hint_y=None, size = self.scrollview.size, spacing = 5, padding = [0, 5, 0, 5])
        self.boxLayout_.bind(minimum_height=self.boxLayout_.setter('height'))
        self.scrollview.add_widget(self.boxLayout_)
        self.build_adress_row()


    def build_adress_row(self):
        flag = SqliteMyDate().check_table_for_save()
        if flag == 1:
            self.build_adress()
        else:
            status = 'Извините, но данные не обнаруженны. Перезагрузите приложение.'
            self.show_status_popup(status)
            return


    def build_adress(self):
        options_list_date = check_table(self.date)
        len_date = len(options_list_date)

        if len_date == 0:
            return

        elif len_date > 0:
            total_distance = 0

            for index in range(len_date):
                self.row += 1
                self.widget = widget_two(padding = [5, 0, 5, 0])
                self.widget.size = (Window.width, Window.height/self.part)
                self.widget.pos = (0, self.pass_widget.pos[1] - self.widget.height - 2 )
                self.widget.canvas_color_text= (1,0,0,1)

                self.boxLayout_.add_widget(self.widget)

                total_distance += options_list_date[index][4]
                
                self.DictAdressStreet.install(row=self.row, widget=self.widget, 
                            address_street=options_list_date[index][1], lon=options_list_date[index][2],
                            lat=options_list_date[index][3], distance=options_list_date[index][4])

                self.widget.ids.address_street.is_focusable = False
                self.widget.ids.address_street.multiline = True
                self.widget.ids.address_street.canvas_color_text= (1,1,1,1)
                self.widget.ids.address_street.text = '{city}'.format(city=options_list_date[index][1])
                
                if self.row < len_date: 
                    self.widget.ids.distance.text = str(self.DictAdressStreet.option[self.row]['distance'])

                self.pass_widget = self.DictAdressStreet.option[self.row]['widget']

        self.FooterWidget.ids.total.text = str(total_distance) + ' км'


    def date_transformation(self, date):
        monts_Str = {
                1 : 'Января',
                2 : 'Февраля',
                3 : 'Марта',
                4 : 'Апреля',
                5 : 'Мая',
                6 : 'Июня',
                7 : 'Июля',
                8 : 'Августа',
                9 : 'Сентября',
                10 : 'Октября',
                11 : 'Ноября',
                12 : 'Декабря',
                }
        months =  monts_Str[date[1]]
        return months


    def add_row(self):
        self.FooterWidget.ids.total.text = ''
        self.FooterWidget.ids.save_button.opacity = 0
        self.FooterWidget.ids.save_button.disabled = True

        if self.row > 24:                 
            return

        self.row += 1
        self.widget = widget_two(padding = [10, 0, 7, 0])
        self.widget.size = (Window.width, Window.height/self.part)
        self.widget.pos = (0, self.pass_widget.pos[1]  )
        self.boxLayout_.add_widget(self.widget)

        self.pass_widget = self.widget
        self.DictAdressStreet.install( row=self.row, widget=self.widget)


    def delete_row(self):
        self.FooterWidget.ids.total.text = ''
        self.FooterWidget.ids.save_button.opacity = 0
        self.FooterWidget.ids.save_button.disabled = True
        self.DictAdressStreet.delete_row(self, self.row)
        self.row -= 1


    def calculate_distance(self, inst, i):
        amount_key = self.DictAdressStreet.option.keys()
        self.len_amount_key = len(amount_key)

        if self.len_amount_key < 2:
            status = "Мало данных\nдля расчетов"

        elif self.len_amount_key > 1:
            try:
                for key in amount_key:
                    self.DictAdressStreet.option[key]['address_street']

            except KeyError:
                status = "Введите данные"

            else:
                try:
                    for key in amount_key:
                        self.DictAdressStreet.option[key]['distance']
                        
                except KeyError:
                    self.content = CircularProgressBar()
                    self._popup = Popup(title="", content=self.content, separator_height = 0, auto_dismiss=False,
                                        background =  './data/img/f.png', opacity = 1, size_hint=(0.3, 0.3))
                    self._popup.open()
                    threading.Thread(target=partial(self.calculate_distance_route)).start()
                    return

                else: 
                    status = "Данные\nне изменились"

        self.show_status_popup(status)


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0,
                                background =  './data/img/f.png', opacity = 1, size_hint=(0.3, 0.1))
        self._popup.open()


    def calculate_distance_route(self):
        total_distance = 0
        check_value = 0
        value = 100 / self.len_amount_key
        client = openrouteservice.Client(BeginConfiguration.key, timeout = 15) # Specify your personal API key


        try:
            for key in range(self.len_amount_key):
                if key == 0:
                    addr_1= self.DictAdressStreet.option[key+1]['lon'], self.DictAdressStreet.option[key+1]['lat']
                    widget = self.DictAdressStreet.option[key+1]['widget']
                    label_1 = widget.ids.distance
                    addr_1_street = self.DictAdressStreet.option[key+1]['address_street']
                    
                elif key > 0:
                    addr_2= self.DictAdressStreet.option[key+1]['lon'], self.DictAdressStreet.option[key+1]['lat']
                    addr_2_street = self.DictAdressStreet.option[key+1]['address_street']

                    coords = ((addr_1),( addr_2 ))
                    route = client.directions(coords)
                    if 'distance' in route['routes'][0]['summary']:             # обработчик ошибки KeyError
                        distance = route['routes'][0]['summary']['distance']
                        distance = distance / 1000
                        distance = math.ceil(distance +  (distance/6))                  

                    else:
                        distance = 0

                    check_value += value
                    Clock.schedule_once(partial(self.animate, check_value))
                    addr_1 = addr_2
                    addr_1_street = addr_2_street

                    label_1.text = str(distance)
                    self.DictAdressStreet.option[key]['distance'] = distance
                    total_distance += distance

                    widget = self.DictAdressStreet.option[key+1]['widget']
                    label_1 = widget.ids.distance
                    self.FooterWidget.ids.total.text = str(total_distance) + ' км'

        except openrouteservice.exceptions.Timeout:
            self._popup.dismiss()
            status = 'сервер не отвечает\nпроверьте интеренет соединение'

        except openrouteservice.exceptions.ApiError:
            self._popup.dismiss()
            status='невозможно найти дорогу\n{addr_1} -- \n {addr_2}'.format(addr_1=addr_1_street,addr_2=addr_2_street)       

        except:
            self._popup.dismiss()
            status = 'проверьте\nинтеренет соединение'

        else:
            status = "ГОТОВО"
            self.DictAdressStreet.option[key+1]['distance'] = 0             
            self.FooterWidget.ids.save_button.opacity = 1
            self.FooterWidget.ids.save_button.disabled = False
            self._popup.dismiss()

        finally:
            self.show_status_popup(status)


    def animate(self, check_value, *args ):
        self.content.set_value(check_value)
        

    def change_total_distance(self):                    
        self.FooterWidget.ids.total.text = ''
        self.FooterWidget.ids.save_button.opacity = 0
        self.FooterWidget.ids.save_button.disabled = True


    def save_to_sqlite(self):
        status = update_insert( self.date, self.DictAdressStreet)
        self.show_status_popup(status)
        self.FooterWidget.ids.save_button.opacity = 0
        self.FooterWidget.ids.save_button.disabled = True
        


class HomeScreen(Screen):
    part = 15                                                  # TODO
    savefile = ObjectProperty(None)
    count = NumericProperty()


    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.headerWidget = HeaderWidget()
        self.headerWidget.size = (Window.width, Window.height/12)
        self.headerWidget.pos = (0, Window.height - self.headerWidget.height)
        self.headerWidget.ids.home_back.disabled = True
        self.headerWidget.ids.home_back.opacity = 0
        self.add_widget(self.headerWidget)

        self.footer = Footer()
        self.footer.size = (Window.width, Window.height/14)
        self.footer.pos = (0, 0)
        self.add_widget(self.footer)

        self.widget_three  = widget_three()
        self.widget_three.pos = (0,  self.footer.height   )
        self.widget_three.size = (Window.width, Window.height -  self.headerWidget.height - self.footer.height  )
        self.add_widget(self.widget_three)

        self.build_widget()


    def cashe_append(self):
        key = 'cashe_waybill'
        wb = openpyxl.load_workbook(filename = Calculate.FILE_READ_XLSX)
        Cache.append('mycache', key, wb)                         # TODO кеш
        wb.close()


    def remove_cashe(self, inst):
        threading.Thread(target=partial(Cache.remove, 'mycache', 'cashe_waybill' )).start()
        p = Cache.get("mycache", 'cashe_waybill')


    def build_widget(self):
        family = Calculate.config_file_get('mydata', 'family')
        if len(family) > 0:
            self.widget_three.ids.family.text = family
            self.widget_three.ids.family.canvas_color_text = 1,1,1,1

        car = Calculate.config_file_get('mydata', 'car')
        if len(car) > 0:
            self.widget_three.ids.car.text = car
            self.widget_three.ids.car.canvas_color_text = 1,1,1,1

        number_car = Calculate.config_file_get('mydata', 'carnumber')
        if len(number_car) > 0:
            self.widget_three.ids.number_car.text = number_car
            self.widget_three.ids.number_car.canvas_color_text = 1,1,1,1


    def dismiss_popup(self):
        self._popup.dismiss()


    def show_save(self):
        self.dateBegin = date(MyClass.date_begin[2], MyClass.date_begin[1], MyClass.date_begin[0])
        self.dateEnd = date(MyClass.date_end[2], MyClass.date_end[1], MyClass.date_end[0])
            
        if self.dateBegin > self.dateEnd :
            status = "неверные даты"
            
        elif self.dateBegin <= self.dateEnd:
            bd = SqliteMyDate()
            flag = bd.check_table_for_save()

            if flag == 1:
                self._check_date()
                return
            else:
                status = 'Извините, но данные не обнаруженны. Перезагрузите приложение.'
            
        self.show_status_popup(status)

    
    def _check_date(self):
        status_check_date , status, MyClass.count = check_date(self.dateBegin, self.dateEnd)
        if status_check_date == True:
            if Calculate.OS_PLATFORM == 'linux':
                            
                self.content = SaveDialog( cancel=self.dismiss_popup )
                self._popup = Popup(title="", content=self.content, background =  './data/img/f.png', 
                                    opacity = 1, size_hint=(0.8, 0.8))
                self._popup.open()
                return 
            
            elif Calculate.OS_PLATFORM == 'android':
                write = ExcelWrite()
                threading.Thread(target=partial(write.write_to_excel )).start()   
        else:
            self.show_status_popup(status)


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0,
                                background =  './data/img/f.png', opacity = 1, size_hint=(0.3, 0.1))
        self._popup.open()


class CircularProgressBar(ProgressBar):

    def __init__(self, **kwargs):
        super(CircularProgressBar, self).__init__(**kwargs)
        # Set constant for the bar thickness
        self.thickness = 6
        self.draw()


    def draw(self):
        with self.canvas:
            self.size = '50sp', '50sp'                                                             
            self.pos=(Window.width/2 - self.size[0]/2 , Window.height/2 - self.size[1]/2)
            
            self.canvas.clear()

            # Draw no-progress circle
            Color(0.26, 0.26, 0.26)
            Ellipse(pos=self.pos, size=self.size)

            # Draw progress circle, small hack if there is no progress (angle_end = 0 results in full progress)
            Color(1, 0, 0)
            Ellipse(pos=self.pos , size=self.size,
                    angle_end=(0.001 if self.value_normalized == 0 else self.value_normalized*360))

            Color(0, 0, 1, .9)
            Ellipse(pos=(self.pos[0] + self.thickness / 2, self.pos[1] + self.thickness / 2),
                    size=(self.size[0] - self.thickness, self.size[1] - self.thickness))


    def set_value(self, value):
        self.value = value
        self.draw()


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
    color_canvas_text_input = ListProperty([0, 0.5, 1, 0.8])
    color_text_input = ListProperty([0.6, 0.6, 0.6, 0.9])
    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)


    def validate(self, instance, value):
        if len(value) > 15:
            instance.text = value[:-1]
            return

        if len(value) > 0:
            self.color_text_input = 1,1,1,1
        else:
            self.color_text_input = 0.6, 0.6, 0.6, 0.9


    def save(self, path, filename):
        filename = '{filename}.xlsx'.format(filename=filename)
        self.filename = os.path.join(path, filename)
        check_filename = os.path.isfile(self.filename)
        if check_filename:
            self._popup.dismiss()

            status = 'выберите другое\n название файла'
            self.show_status_popup(status)

        elif not check_filename:
            write = ExcelWrite()
            threading.Thread(target=partial(write.write_to_excel, self.filename)).start()


    def my_callback(self, *largs):
        self.remove_widget(self.bubble)


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0,
                                background =  './data/img/f.png', opacity = 1, size_hint=(0.3, 0.1))
        self._popup.open()



class ExcelWrite():

    months_Str = {
                1 : 'Январь',
                2 : 'Февраль',
                3 : 'Март',
                4 : 'Апрель',
                5 : 'Май',
                6 : 'Июнь',
                7 : 'Июль',
                8 : 'Август',
                9 : 'Сентябрь',
                10 : 'Октябрь',
                11 : 'Ноябрь',
                12 : 'Декабрь',
                }


    def write_to_excel(self , filename=None):
        """"""
        self.content = CircularProgressBar()
        self._popup = Popup(title="", content=self.content, separator_height = 0, auto_dismiss=False,
                        background = './data/img/f.png', opacity = 1, size_hint=(0.3, 0.3))
        self._popup.open()

        try:
            dateBegin = date(MyClass.date_begin[2], MyClass.date_begin[1], MyClass.date_begin[0])
            dateEnd = date(MyClass.date_end[2], MyClass.date_end[1], MyClass.date_end[0])

            check_value = 0
            value = 100 / MyClass.count

            count_day = 1
            len_months = 1

            months = set()

            con = sqlite3.Connection(Calculate.FILE_DATA_DISTANCE)
            cur = con.cursor()
            # EXCEL

            wb = Cache.get("mycache", 'cashe_waybill')                   
            list = 'example'                               

            ws = wb[list]                                  
            ws.sheet_state = 'hidden'                           

            for dt in rrule(DAILY, dtstart=dateBegin, until=dateEnd):
                finish = time.time()
                one_day = (dt.strftime("{day}.{month}.%Y").format(day=dt.day, month=dt.month))

                cur.execute('SELECT COUNT(date) from "DateDistance_2" where "date"=?', [one_day])
                row_count = cur.fetchone()[0]

                if row_count == 0:
                    continue

                else:
                    one_months = dt.strftime('{month}.%Y').format(month=dt.month)
                    months.add(one_months)
                    if len_months < len(months):
                        count_day = 1

                    one_date_notice = []

                    for  row_count in range(0 , row_count + 1):
                        for addr_street, distance in cur.execute('''SELECT 
                                    "street" , "distance" 
                                    FROM "DateDistance_2" WHERE "date" = ? and "row_count"=?''', [one_day, row_count, ] ):
                            one_row = [ addr_street, distance]
                            one_date_notice.append(one_row)

                if count_day % 2 != 0:
                    source = ws
                    target = wb.copy_worksheet(source)
                    target.title = one_day

                    self.write_excel_column_one(target, one_day, row_count, one_date_notice)

                elif count_day % 2 == 0:
                    self.write_excel_column_two(target, one_day, row_count, one_date_notice)

                check_value += value
                Clock.schedule_once(partial(self.animate, check_value))

                count_day += 1
                len_months = len(months)

            list = 'home_page'                                         
            ws = wb[list] 
            ws.sheet_state = 'hidden'                       

            for one_month in months:
                one_month_list = one_month.split('.')


                month = self.months_Str[int(one_month_list[0])]
                source = ws
                target = wb.copy_worksheet(source)
                target.title = 'title_{month}'.format(month=one_month)

                target['AI5'] = month
                target['EA5'] = month

                target['AW5'] = one_month_list[1][2:]
                target['EO5'] = one_month_list[1][2:]

                target['V10'] = Calculate.config_file_get('mydata', 'car')                            
                target['DN10'] = Calculate.config_file_get('mydata', 'car')

                target['AI11'] = Calculate.config_file_get('mydata', 'carnumber')                          #! ГОС ЗНАК
                target['EA11'] = Calculate.config_file_get('mydata', 'carnumber')

                target['M12'] = Calculate.config_file_get('mydata', 'family')                  #! Ф.И.О
                target['DE12'] = Calculate.config_file_get('mydata', 'family') 

            cur.close()
            con.close()

            if filename == None:
                dir_file = os.path.join(Calculate.APP_DIR, 'data')
                count = 0
                flag = False

                while flag == False:
                    if count == 0:
                        filename = '{filename}.xlsx'.format(filename=month)
                        filename = os.path.join(dir_file, filename)
                        
                    else:
                        filename = '{filename}({count}).xlsx'.format(filename=month, count=count)
                        filename = os.path.join(dir_file, filename)

                    if (os.path.exists(filename) == False):
                        flag = True
                        break
                    else:
                        count += 1
                        continue

            wb.save(filename)        
            wb.close()

            check_value += value
            Clock.schedule_once(partial(self.animate, check_value))
            status = "ГОТОВО"

            self._popup.dismiss()

        except PermissionError:
            self._popup.dismiss()
            status = 'Здесь нельзя\nсохранять'
        
        self.show_status_popup(status)


    def write_excel_column_one(self, target, one_day, row_count, one_date_notice):

        target['B5'] = one_day[:-5]
        target['F5'] = "9"
        target['H5'] = "00"
        total_distance = 0

        index_RE = 5                            #

        for row in range(row_count):
            total_distance += one_date_notice[row][1]
            address = one_date_notice[row][0]
            if len(address) > 40:
                target['C'+ str(index_RE)].font = Font(size=7)
            elif len(address) < 40:
                target['C'+ str(index_RE)].font = Font(size=8)

            target['C'+ str(index_RE)] = address

            if one_date_notice[row][1] != 0:
                target['K'+ str(index_RE)] = str(one_date_notice[row][1]) + 'км'

            index_RE += 1

        target['D35'] = str(total_distance) + 'км'

        index_RE -= 1
        target['I'+ str(index_RE)] = "18"
        target['J'+ str(index_RE)] = "00"


    def write_excel_column_two(self, target, one_day, row_count, one_date_notice):
        target['Q5'] = one_day[:-5]
        target['U5'] = "9"
        target['W5'] = "00"
        total_distance = 0

        index_RE = 5                            #  обновление индекса для внесения в таблицу Excel 

        for row in range(row_count):
            total_distance += one_date_notice[row][1]

            address = one_date_notice[row][0]
            if len(address) > 40:
                target['R'+ str(index_RE)].font = Font(size=7)
            elif len(address) < 40:
                target['R'+ str(index_RE)].font = Font(size=8)

            target['R'+ str(index_RE)] = address

            if one_date_notice[row][1] != 0:
                target['Z'+ str(index_RE)] = str(one_date_notice[row][1]) + 'км'

            index_RE += 1

        target['S35'] = str(total_distance) + 'км'

        index_RE -= 1
        target['X'+ str(index_RE)] = "18"
        target['Y'+ str(index_RE)] = "00"


    def show_status_popup(self, status, *args):
        content = ErorrPopup()
        content.ids.label_erorr.text = status            
        self._popup = Popup(title="", content=content, separator_height = 0,
                                background =  './data/img/f.png', opacity = 1, size_hint=(0.3, 0.1))
        self._popup.open()


    def animate(self, check_value, *args ):
        self.content.set_value(check_value)


class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)
        flag = Calculate.config_file_get('mydata', 'flag')
        if flag == '1':
            self.add_widget(FirstScreenOne(name='FirstScreenOne'))
            self.current = 'FirstScreenOne'

        if flag == '0':
            self.add_widget(FirstScreenTwo(name='FirstScreenTwo'))
            self.current = 'FirstScreenTwo'

    def add_screen_manager(self, date_now):                                              # TODO ONE METOD
        self.clear_widgets(self.children)
        self.add_widget(SecondScreen(name='SecondScreen', date=date_now))
        self.current = 'SecondScreen'


    def remove_screen_manager(self):        
        self.clear_widgets(self.children)
        self.add_widget(FirstScreen(name='FirstScreen'))
        self.current = 'FirstScreen'


    def home_screen_manager(self):
        self.clear_widgets(self.children)
        self.add_widget(HomeScreen(name='HomeScreen'))
        self.current = 'HomeScreen'


    def first_screen_two(self):
        self.clear_widgets(self.children)
        self.add_widget(FirstScreenTwo(name='FirstScreenTwo'))
        self.current = 'FirstScreenTwo'

    
    def first_screen(self, dt):
        self.clear_widgets(self.children)
        self.add_widget(FirstScreen(name='FirstScreen'))
        self.current = 'FirstScreen'



class Calculate(App):
    FILE_DATA_ASTRAKHAN = './data/astrakhan.sqlite'
    FILE_READ_XLSX = './data/waybill.xlsx'

    FILE_DATA_DISTANCE = ''
    MY_TABLE_ONE = "DateDistance"
    MY_TABLE_TWO = "DateDistance_2"

    OS_PLATFORM  = ''
    APP_DIR = ''


    def config_file_get( *args):
        arg = args
        return Config.get(arg[0], arg[1])


    def config_file_set( *args):
        arg = args
        Config.set(arg[0], arg[1], arg[2])
        Config.write()

    def build(self):
        BeginConfiguration()

        if self.OS_PLATFORM == 'linux':
            Factory.register('SaveDialog', cls=SaveDialog)
        if self.OS_PLATFORM == 'android':
            Window.softinput_mode = "below_target"
        Cache.register('mycache')
        
        
        def cashe_append():
            key = 'cashe_waybill'
            wb = openpyxl.load_workbook(filename = self.FILE_READ_XLSX)
            Cache.append('mycache', key, wb)                         # TODO кеш
            wb.close()

        threading.Thread(target=partial(cashe_append)).start()

        sm = ScreenManagement()
        return sm


if __name__ in ('__main__', '__android__'):
    Calculate().run()