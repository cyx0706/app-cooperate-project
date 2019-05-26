# -*- coding:utf-8 -*-

from django.core.paginator import Paginator
from django.utils.translation import ugettext_lazy as _
import math
import logging
class IDNotExist(Exception):
    pass

class IDNotInteger(Exception):
    pass


class DynamicPaginator(Paginator):
    """
    override Django inside Paginator to avoid that
    if you add a new data in database, then the last strip of data in last page
    will be the first strip of next page
    Remember!! If you want to use this, please make sure your newest data is placed
    at the first of database' table
    """
    def __init__(self, object, per_page, orphans=0, lastId=0,
                 allow_empty_first_page=True):
        self.lastId = lastId
        self.object = object
        super(DynamicPaginator, self).__init__(list(object), per_page, orphans,
                                               allow_empty_first_page)
        self.checklastId()

    def checklastId(self):
        if self.lastId == 0 and self.object_list:
            self.lastId = self.object_list[0].id
        else:
            try:
                self.lastId = int(self.lastId)
            except (TypeError, ValueError):
                raise IDNotInteger(_("That ID Must Be Integer"))

    def page(self, number):
        object_list = self.object.filter(id__lt=self.lastId)
        print(self.lastId)
        if not object_list:
            raise IDNotExist(_("That ID of Data Does Not Exist"))
        number = self.validate_number(number)
        bottom = number - 1
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(object_list[bottom:top], number, self)

info_log = logging.getLogger('info')

class PaginatorThroughLast():

    def __init__(self, object_queryset, per_page, lastId):
        self.lastId = lastId
        self.id_list = list(object_queryset.values_list('id', flat=True))
        self.queryset_list = object_queryset
        self.per_page = per_page
        self.count_page()
        self.checklastId()

    def count_page(self):
        self.page_number = int(math.ceil(len(self.queryset_list) / self.per_page))

    def total_page(self):
        return self.page_number

    def checklastId(self):
        if self.lastId == 0:
            self.lastId = self.id_list[0]
        else:
            try:
                self.lastId = int(self.lastId)
            except (TypeError, ValueError):
                raise IDNotInteger(_("That ID Must Be Integer"))

    def page(self):
        num = 0
        for i in self.id_list:
            if i == self.lastId:
                break
            num += 1
        begin = num
        end = begin + self.per_page
        return self.queryset_list[begin: end]
        # self.object_queryset = self.object_queryset.filter(id__lt=self.lastId)
        # return self.object_queryset[0: self.per_page]
