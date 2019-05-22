# -*- coding:utf-8 -*-

from django.core.paginator import Paginator
from django.utils.translation import ugettext_lazy as _

class IDNotExist(Exception):
    pass

class IDNotInteger(Exception):
    pass

class DynamicPaginator(Paginator):
    """
    override Django inside Paginator to avoid that
    if you add a new data in database, then the last strip of data in last page
    will be the first strip of next page

    """
    def __init__(self, object_list, per_page, orphans=0, lastId=0,
                 allow_empty_first_page=True):
        self.lastId = lastId
        self.checklastId()
        super(DynamicPaginator, self).__init__(object_list, per_page, orphans,
                                               allow_empty_first_page)

    def checklastId(self):
        if self.lastId == 0:
            pass
        else:
            try:
                self.lastId = int(self.lastId)
            except (TypeError, ValueError):
                raise IDNotInteger(_("That ID Must Be Integer"))

    def page(self, number):
        object_list = self.object_list.filer(id__lt=self.lastId)
        if not object_list:
            raise IDNotExist(_("That ID of Data Does Not Exist"))
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.object_list[bottom:top], number, self)

