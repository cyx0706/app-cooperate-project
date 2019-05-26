from django.contrib import admin
from app_api.models import *
from app_api import forms
from django.utils.safestring import mark_safe
import hashlib
import uuid
import random

admin.site.disable_action('delete_selected')


# class UserEXInfo(admin.StackedInline):
#     model = UserDetailMsg
#     fk_name = 'user'
#
#     verbose_name_plural = "详细个人信息"
#     verbose_name = verbose_name_plural

@admin.register(UserDetailMsg)
class UserExAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ['get_username', 'gender', 'get_user_id']
    filter_horizontal = ('collections', 'interest')
    # readonly_fields = ['user']


    # def has_add_permission(self, request):
    #     return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UserAll)
class UserAdmin(admin.ModelAdmin):

    list_per_page = 5
    list_display = ['id', 'username', 'email', 'get_avatar', 'status']
    # inlines = [UserEXInfo]
    search_fields = ['username', 'email']
    list_filter = (
        ('status', admin.BooleanFieldListFilter),
    )
    form = forms.UserForm

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        if obj:
            return ['username', 'email', 'avatar', 'status']
        else:
            return ['username', 'email', 'avatar', 'status', 'password']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['username']
        else:
            return []

    # def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
    #     if obj:
    #         return [UserEXInfo]
    #     else:
    #         return []

    def block_user(self, request, queryset):
        row_updated = queryset.update(status=False)
        message_bit = "屏蔽了%s个用户" % row_updated
        self.message_user(request, message_bit)
    block_user.short_description = "注销用户"
    actions = [block_user]

    def save_model(self, request, obj, form, change):
        if not form.is_valid():
            pass
        if not change:
            obj.password = hashlib.sha1(form.cleaned_data.get('password').encode('utf-8')).hexdigest()
            obj.username = form.cleaned_data.get('username')
        super().save_model(request, obj, form, change)
        if not change:
            user = UserAll.objects.get(username=obj.username)
            UserDetailMsg.objects.create(user=user)



@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):

    list_display = ['type']

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
    list_display = ['name', 'get_master', 'create_time', 'bar_number', 'id']
    list_filter = (
        (PostBarTagsFilter),
    )

    search_fields = ['name', 'master__username']
    readonly_fields = ['get_pic']


class PhotoInline(admin.TabularInline):
    model = PostPhotos
    fk_name = 'post'
    max_num = 5


class PostBarFilter(admin.SimpleListFilter):

    title = "按类型分类"
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return ((t.id, t.name) for t in PostBars.objects.all())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bar_id=self.value())
        else:
            return queryset


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):

    list_display = ['id','title', 'create_time', 'get_writer', 'get_bar', 'display_status']
    list_per_page = 10
    inlines = [PhotoInline]
    search_fields = ['content', 'writer__username']
    list_filter = (
        (PostBarFilter),
    )



class FloorCommentInline(admin.TabularInline):
    model =FloorComments
    fk_name = 'reply'
    fields = ['user', 'content']
    max_num = 2


class PostListFilter(admin.SimpleListFilter):
    title = "按吧分"
    parameter_name = 'by_bar'

    def lookups(self, request, model_admin):
        return ((t.id, t.name) for t in PostBars.objects.all())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(post__bar=self.value())
        else:
            return queryset


@admin.register(PostFloor)
class PostFloorAdmin(admin.ModelAdmin):

    list_per_page = 15
    list_display = ['id','get_post', 'get_user', 'floor_number']
    inlines = [FloorCommentInline,]
    list_filter = (
        (PostListFilter),
    )
    search_fields = ['post__title']

    def get_readonly_fields(self, request, obj=None):
        # 只允许创建时选择帖
        if not obj:
            self.readonly_fields = ['floor_number']
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
    list_display = ['id', 'display_status', 'get_description']
    list_filter = (
        ('display_status', admin.BooleanFieldListFilter),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['mutual_following']
        else:
            return []

    def save_model(self, request, obj, form, change):
        if not change:
            user = form.cleaned_data['user']
            follower = form.cleaned_data['follower']
            mutual_following = form.cleaned_data['mutual_following']
            follow = UserFollow.objects.filter(user__user=follower, follower=user.user, display_status=True)
            if follow:
                follow.update(mutual_following=True)
                obj.mutual_following = True
            else:
                if mutual_following:
                    UserFollow.objects.update_or_create(user=follower.user_msg, follower=user.user, defaults={'display_status': True, 'mutual_following': True})
        super().save_model(request, obj, form, change)



@admin.register(SensitiveWord)
class SensitiveWordAdmin(admin.ModelAdmin):
    list_per_page = 20
    actions = ['delete_words',]
    list_display = ['word']

    def delete_words(self, request, queryset):
        row_updated = queryset.delete()
        message_bit = "删除了%s个敏感词" % list(row_updated)[0]
        self.message_user(request, message_bit)
    delete_words.short_description = "删除敏感词"

