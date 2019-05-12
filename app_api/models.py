from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
import uuid
import os


def avatar_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:10], ext)
    return os.path.join("avatar", filename)


def photo_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:10], ext)
    return os.path.join("photo", filename)


class Tags(models.Model):
    type = models.CharField(u'标签', max_length=20)

    def __str__(self):
        return self.type

    class Meta:
        verbose_name = "贴吧类型"
        verbose_name_plural = verbose_name


class PostBars(models.Model):

    photo = models.ImageField(u'吧图标', default='no_picture.jpg', upload_to=photo_path)
    name = models.CharField(u'吧名', max_length=30)
    feature = models.ManyToManyField(Tags, verbose_name="类型")
    master = models.ForeignKey('UserAll', related_name='bar_owner', on_delete=models.CASCADE, verbose_name="用户")
    bar_number = models.IntegerField(u'帖子数', default=0)
    create_time = models.DateTimeField(u'创吧时间', default=timezone.now)
    short_description = models.TextField(u'吧的简介', default="无")

    def get_pic(self):
        url = self.photo.url
        if url:
            return mark_safe("<img src='{}' width=75px height=75px></img>".format(url))
        else:
            return "暂无图片"

    def get_master(self):
        return self.master.username
    get_master.short_description = "吧主"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-create_time']
        verbose_name = "吧"
        verbose_name_plural = verbose_name
        index_together = ['name', 'master', 'create_time']


class Post(models.Model):

    bar = models.ForeignKey(PostBars, related_name='post_bar', on_delete=models.CASCADE, verbose_name="所属吧")
    writer = models.ForeignKey('UserAll', related_name='post_writer', verbose_name="作者")
    title = models.CharField(u'帖子标题', max_length=20)
    content = models.TextField(u'帖子内容')
    create_time = models.DateTimeField(u'发帖时间', default=timezone.now)
    display_status = models.BooleanField(u'帖子展示状态', default=True)

    class Meta:
        ordering = ['-create_time']
        verbose_name = "帖子"
        verbose_name_plural = verbose_name
        index_together = ['create_time', 'title']

    def __str__(self):
        return self.title

    def get_bar(self):
        return self.bar.name
    get_bar.short_description = "所属吧"

    def get_writer(self):
        return self.writer.username
    get_writer.short_description = "作者"

    # 保存时在吧里增加1条帖子
    def save(self, *args, **kwargs):
        # 已经存在
        if Post.objects.filter(id=self.id):
            super(Post, self).save(*args, **kwargs)
        # 生成楼层对应1楼
        else:
            bar = self.bar
            bar.bar_number += 1
            bar.save()
            super(Post, self).save(*args, **kwargs)
            floor1 = PostFloor(user=self.writer, content=self.content, floor_number=1)
            floor1.post_id = self.id
            floor1.save()

    # 删除时减1条
    def delete(self, *args, **kwargs):
        bar = self.bar
        bar.bar_number -= 1
        bar.save()
        super(Post, self).delete(*args, **kwargs)


# 楼中楼把楼和评论分成两张表最好
class PostFloor(models.Model):
    # 记得默认贴吧内容为1楼, 这些楼从2楼开始
    post = models.ForeignKey(Post, related_name='post_floor', on_delete=models.CASCADE, verbose_name="帖子")
    user = models.ForeignKey('UserAll', related_name='floor_writer', on_delete=models.CASCADE, verbose_name="作者")
    content = models.TextField(u'楼层评论内容')
    create_time = models.DateTimeField(u'发楼层时间', default=timezone.now)
    unfold_status = models.BooleanField(u'楼层展示状态', default=True)
    floor_number = models.PositiveIntegerField(u'楼层数')
    read_status = models.BooleanField(u'楼主已读状态', default=False)
    display_status = models.BooleanField(u'消息展示状态', default=True)

    class Meta():
        verbose_name = "楼"
        verbose_name_plural = "楼"
        ordering = ['-create_time']
        index_together = ['create_time']

    def __str__(self):
        return "{}帖{}楼".format(self.post.title, self.floor_number)

    def get_post(self):
        return self.post.title
    get_post.short_description = "所属吧"

    def get_user(self):
        return self.user.username
    get_user.short_description = "发表用户"

    def save(self, *args, **kwargs):
        # 指定楼层
        if self.floor_number:
            print(self.floor_number)
        else:
            # 楼层数+1
            self.floor_number = list(PostFloor.objects.filter(post_id=self.post_id).values_list('floor_number', flat=True))[0] + 1
        super(PostFloor, self).save(*args, **kwargs)


class FloorComments(models.Model):

    reply = models.ForeignKey(PostFloor, related_name='floor_comment', on_delete=models.CASCADE, verbose_name="回复的楼")
    user = models.ForeignKey('UserAll', related_name='comment_user', on_delete=models.CASCADE, verbose_name="作者")
    replied_comment = models.IntegerField(u'回复评论', default=0)
    content = models.TextField(u'评论内容')
    create_time = models.DateTimeField(u'发评论时间', default=timezone.now)
    read_status = models.BooleanField(u'评论消息已读状态', default=False)
    status = models.BooleanField(u'评论显示状态', default=True)
    display_status = models.BooleanField(u'消息展示状态', default=True)

    class Meta():
        ordering = ['-create_time']
        verbose_name = "评论"
        verbose_name_plural = "评论"
        index_together = ['create_time']

    def get_user(self):
        return self.user.username
    get_user.short_description = "发表人"

    def get_floor(self):
        return self.reply.floor_number
    get_floor.short_description = "评论楼层"

    def get_post(self):
        return self.reply.post.title
    get_post.short_description = "所属帖子"

    def get_reply_status(self):
        if self.replied_comment == 0:
            return "-"
        else:
            return "回复id={}".format(self.replied_comment)
    get_reply_status.short_description = "回复状态"


class PostPhotos(models.Model):
    post = models.ForeignKey(Post, related_name='post_photo', on_delete=models.CASCADE)
    pic = models.ImageField(u'帖子图片', upload_to='photo/%Y/%m')

    class Meta:
        verbose_name = "图片"
        verbose_name_plural = "图片"

    def save(self, *args, **kwargs):
        self.pic.name = '{}.jpg'.format(''.join(str(uuid.uuid4()).split('-')))
        super(PostPhotos, self).save(*args,**kwargs)


class UserAll(models.Model):
    username = models.CharField(u'姓名', max_length=50)
    password = models.CharField(u'密码', max_length=100)
    email = models.EmailField(u'邮箱', max_length=30)
    avatar = models.ImageField(u'头像', default='avatar_default.jpg', upload_to=avatar_path, blank=True)
    status = models.BooleanField(u'用户状态', default=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "全部用户"
        index_together = ['username', 'email']


    def get_avatar(self):
        url = self.avatar.url
        if url:
            return mark_safe('<img src="{}" width="50px"></img>'.format(url))
        else:
            return "暂无图片"
    get_avatar.short_description = "头像缩略图"


class UserDetailMsg(models.Model):

    GENDER_CHOICE = (
        (0, "男"),
        (1, "女"),
        (2, "保密")
    )
    user = models.OneToOneField('UserAll', verbose_name='用户id', related_name='user_msg')
    birthday = models.DateField(u'生日', blank=True, null=True)
    gender = models.IntegerField(u'性别', choices=GENDER_CHOICE, blank=True, default=2)
    description = models.TextField(u'个人简介', blank=True)
    background_pic = models.ImageField(u'个人中心背景', upload_to=photo_path, blank=True)

    watching = models.ManyToManyField(PostBars, verbose_name='关注的吧', through='UserWatching')
    collections = models.ManyToManyField(Post, verbose_name='收藏的帖子', related_name='user_collection', blank=True)
    interest = models.ManyToManyField(Tags, verbose_name='兴趣', blank=True)
    follow = models.ManyToManyField(UserAll, verbose_name='关注', through='UserFollow')
    praise = models.ManyToManyField(Post, verbose_name="点赞的帖子", blank=True, through='UserPraise', related_name='user_praise')

    def __str__(self):
        return self.user.username


class UserPraise(models.Model):
    user = models.ForeignKey(UserDetailMsg, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    time = models.DateTimeField(u'时间', default=timezone.now)
    read_status = models.BooleanField(u'消息已读状态', default=False)
    info_status = models.BooleanField(u'消息展示状态', default=True)
    display_status = models.BooleanField(u'展示状态', default=True)

    class Meta:
        verbose_name_plural = "点赞"
        verbose_name = "点赞"

    def get_user(self):
        return self.user.user.username
    get_user.short_description = "用户名"

    def get_post(self):
        return self.post.title
    get_post.short_description = "帖子名"


class UserFollow(models.Model):
    user = models.ForeignKey(UserDetailMsg, on_delete=models.CASCADE)
    follower = models.ForeignKey(UserAll, on_delete=models.CASCADE)
    time = models.DateTimeField(u'时间', default=timezone.now)
    mutual_following = models.BooleanField(u'互相关注状态',default=False)
    read_status = models.BooleanField(u'消息已读状态', default=False)
    info_status = models.BooleanField(u'消息展示状态', default=True)
    display_status = models.BooleanField(u'展示状态', default=True)

    class Meta:
        verbose_name_plural = "用户关注的人"
        verbose_name = verbose_name_plural

    def __str__(self):
        return self.user.user.username + "关注:" + self.follower.username


class UserWatching(models.Model):
    user = models.ForeignKey(UserDetailMsg, on_delete=models.CASCADE)
    bar = models.ForeignKey(PostBars, on_delete=models.CASCADE)
    time = models.DateTimeField(u'时间', default=timezone.now)
    read_status = models.BooleanField(u'消息已读状态', default=False)
    info_status = models.BooleanField(u'消息展示状态', default=True)
    display_status = models.BooleanField(u'展示状态', default=True)

    class Meta:
        verbose_name_plural = "用户关注的吧"
        verbose_name = verbose_name_plural

    def __str__(self):
        return self.user.user.username + "关注:" + self.bar.name


class SensitiveWord(models.Model):
    word = models.CharField(u'敏感词', max_length=40)

    class Meta:
        verbose_name_plural = "敏感词"
        verbose_name = verbose_name_plural

    def __str__(self):
        return self.word



