from django.contrib import admin
from app_api.models import *
from app_api import forms
from django.utils.safestring import mark_safe
import hashlib
import uuid
import random

admin.site.disable_action('delete_selected')


class UserEXInfo(admin.StackedInline):
    model = UserDetailMsg
    fk_name = 'user'
    filter_horizontal = ('collections', 'interest')



@admin.register(UserAll)
class UserAdmin(admin.ModelAdmin):

    list_per_page = 5
    list_display = ['id', 'username', 'email', 'get_avatar', 'status']
    inlines = [UserEXInfo]
    search_fields = ['username', 'email']
    list_filter = (
        ('status', admin.BooleanFieldListFilter),
    )

    def block_user(self, request, queryset):
        row_updated = queryset.update(status=False)
        message_bit = "屏蔽了%s个用户" % row_updated
        self.message_user(request, message_bit)
    block_user.short_description = "注销用户"
    actions = [block_user]

    def save_model(self, request, obj, form, change):
        obj.password = hashlib.sha1(obj.password.encode('utf-8')).hexdigest()
        super().save_model(request, obj, form, change)


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):

    list_display = ['type']
    list_display_links = None

    def delete_tag(self, request, queryset):
        for i in queryset:
            print(i)
            if PostBars.objects.filter(feature=i):
                self.message_user(request, "{}类型已经有贴吧在使用".format(str(i.type)))
                return
        row_updated = queryset.delete()
        message_bit = "删除了%s个类型" % list(row_updated)[0]
        self.message_user(request, message_bit)
    delete_tag.short_description = "删除标签"

    actions = [delete_tag]


class PostBarTagsFilter(admin.SimpleListFilter):

    title = "按类型分类"
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return ((t.id, t.type) for t in Tags.objects.all())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(feature__id=self.value())
        else:
            return queryset


@admin.register(PostBars)
class PostBarsAdmin(admin.ModelAdmin):

    list_per_page = 10
    list_display = ['name', 'get_master', 'create_time', 'bar_number']
    list_filter = (
        (PostBarTagsFilter),
    )

    search_fields = ['name', 'master__username']
    readonly_fields = ['get_pic', 'bar_number']


class PhotoInline(admin.TabularInline):
    model = PostPhotos
    fk_name = 'post'
    max_num = 5


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):

    list_display = ['title', 'create_time', 'get_writer', 'get_bar', 'display_status']
    list_per_page = 10
    inlines = [PhotoInline]


class FloorCommentInline(admin.TabularInline):
    model =FloorComments
    fk_name = 'reply'
    fields = ['user', 'content']
    max_num = 2


@admin.register(PostFloor)
class PostFloorAdmin(admin.ModelAdmin):

    list_per_page = 15
    list_display = ['id','get_post', 'get_user', 'floor_number']
    readonly_fields = ['floor_number']
    inlines = [FloorCommentInline,]

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.readonly_fields
        else:
            self.readonly_fields = ['floor_number', 'post']
            return self.readonly_fields


class LevelCommentFilter(admin.SimpleListFilter):
    title = "评论"
    parameter_name = 'comment'

    def lookups(self, request, model_admin):
        return (
            ('level1', "一级评论"),
            ('level2', "回复评论"),
        )

    def queryset(self, request, queryset):
        if self.value() == 'level1':
            return queryset.filter(replied_comment=0)
        elif self.value() == 'level2':
            return queryset.filter(replied_comment__gt=0)
        else:
            return queryset


@admin.register(FloorComments)
class FloorCommentAdmin(admin.ModelAdmin):

    list_per_page = 20
    list_display = ['id', 'get_user', 'get_post', 'get_floor', 'status', 'get_reply_status']
    list_select_related = ['reply', 'user']
    list_filter = (
        ('status', admin.BooleanFieldListFilter),
        (LevelCommentFilter),
    )
    form = forms.CommentForm

    # def get_readonly_fields(self, request, obj=None):
    #     if not obj:
    #         self.readonly_fields = []
    #     else:
    #         self.readonly_fields = ['reply']
    #     return self.readonly_fields

    def save_model(self, request, obj, form, change):
        replied_comment = form.cleaned_data['replied_comment']
        obj.replied_comment = replied_comment
        super().save_model(request, obj, form, change)


@admin.register(UserWatching)
class UserWatchingAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ['id', 'display_status']
    list_filter = (
        ('display_status', admin.BooleanFieldListFilter),
    )


@admin.register(UserPraise)
class UserPraiseAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ['id', 'get_user', 'get_post', 'display_status']
    list_filter = (
        ('display_status', admin.BooleanFieldListFilter),
    )

@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ['id', 'display_status']
    list_filter = (
        ('display_status', admin.BooleanFieldListFilter),
    )


@admin.register(SensitiveWord)
class SensitiveWordAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display_links = None
    actions = ['delete_words',]
    list_display = ['word']

    def delete_words(self, request, queryset):
        row_updated = queryset.delete()
        message_bit = "删除了%s个敏感词" % list(row_updated)[0]
        self.message_user(request, message_bit)
    delete_words.short_description = "删除敏感词"

