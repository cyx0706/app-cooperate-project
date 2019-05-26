from django.shortcuts import render, HttpResponse
from MyTieba import settings
from django.db.models import Max, Avg, F, Q, Min, Count, Sum
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.views.decorators.cache import cache_page
from app_api.models import *
import json
import re
import hashlib
import random
import threading
import logging
from app_api.DFA_Filter import DFAFilter
from app_api.DynamicPaginator import DynamicPaginator, PaginatorThroughLast, IDNotInteger
info_log = logging.getLogger('info')



def test_session(request):
    if request.method == 'GET':
        request.session['test'] = 'test'
        return JsonResponse({'msg': "存储session成功"})
    if request.method == 'POST':
        if request.session.get('test'):
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False})


def test_delete(request):
    if request.method == 'DELETE':
        name = request.DELETE.get('name', None)
        if name:
            return JsonResponse({'status': True,
                                 'msg': "你成功使用了delete请求!",
                                 'name': name,
                                 'tips': "这里的name的值是你表单里的值"})
        else:
            return JsonResponse({'status': False,
                                 'msg': "你貌似没传上值",
                                 'tips': "确保你的表单字段里的key是name"})
    else:
        return JsonResponse({'status': False, 'msg': "请使用delete请求!"})


def test_sensitive_word(request):
    gfw = DFAFilter()
    path = settings.BASE_DIR.replace('\\','/') + "/app_api/sensitive_words.txt"
    print(path)
    gfw.io_parse(path)
    gfw.database_parse()
    text = "你真是个大傻逼，大傻子，傻大个，大坏蛋，坏人。"
    result = gfw.filter(text)
    print(text)
    print(result)
    return JsonResponse({})


def test_list(request):
    output = []
    list1 = request.POST.getlist('list')
    for x in list1:
        output.append(x)
    return JsonResponse({'list': output})


class JsonResponse(HttpResponse):
    def __init__(self, content,
                 status=None,
                 content_type='application/json',
                 charset='UTF-8'):
        super(JsonResponse, self).__init__(json.dumps(content),
                                           status=status,
                                           content_type=content_type,
                                           charset=charset)


def check_email(email):
    email_flag = re.compile('^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
    if re.match(email_flag, email):
        return True
    else:
        return False


class UserClass():

    def __init__(self, id=0, name=None):
        self.id = id
        self.username = name

    def login(self, password):
        if self.check_name(self.username) and self.check_pwd(password):
            user = UserAll.objects.filter(username=self.username)
            if user:
                user = user[0]
                if hashlib.sha1(password.encode('utf-8')).hexdigest() == user.password:
                    return user
        return None

    def check_name(self, name):
        if name and re.match(r'^\w+$', name):
            return True
        else:
            return False

    def check_pwd(self, password):
        if len(password) > 0:
            return True
        else:
            return False

    # 指定id检查
    def check_user(self):
        if UserAll.objects.filter(id=self.id):
            return True
        else:
            return False

    def upload_avatar(self, request):
        user = UserAll.objects.get(id=self.id)
        pic = request.FILES.get('pic')
        suffix = os.path.splitext(pic.name)[1]
        if not suffix:
            return False
        if suffix.lower() == '.jpeg' or suffix.lower() == ".png" or suffix.lower() == ".jpg":
            if pic._size > settings.MAX_UPLOAD_SIZE:
                return False
            else:
                user.avatar = pic
                user.save()
                return True
        return False

    def check_uniqueness_name(self):
        if UserAll.objects.filter(username=self.username):
            return False
        return True

    def revise_pwd(self, old_pwd, new_pwd):
        if not self.username:
            self.username = UserAll.objects.get(id=self.id).username
        if self.check_pwd(old_pwd) and self.check_pwd(new_pwd):
            user = self.login(old_pwd)
            if user:
                user.password = hashlib.sha1(new_pwd.encode('utf-8')).hexdigest()
                user.save()
                return True
            else:
                return False
        else:
            return False


class UserClassForProject(UserClass):

    def __init__(self, id=0, name=None):
        super().__init__(id, name)

    def create_user(self, password, email, interest, description, birthday, gender):
        if self.check_pwd(password):
            user = UserAll(username=self.username, email=email,
                           password=hashlib.sha1(password.encode('utf-8')).hexdigest())
            user.save()
            user_msg = UserDetailMsg(user=user)
            user_msg.save()
            exist_list = list(Tags.objects.values_list('type', flat=True))
            if interest:
                for x in interest:
                    if x in exist_list:
                        user_msg.interest.add(Tags.objects.get(type=x))
                    else:
                        continue
            if description:
                user_msg.description = description
            if birthday:
                user_msg.birthday = birthday
            user_msg.gender = int(gender)
            user_msg.save()
            return True
        else:
            return False

    def upload_background(self, request):
        user = UserAll.objects.get(id=self.id)
        pic = request.FILES.get('pic')
        suffix = os.path.splitext(pic.name)[1]
        if not suffix:
            return False
        if suffix.lower() == '.jpeg' or suffix.lower() == ".png" or suffix.lower() == ".jpg":
            if pic._size > settings.MAX_UPLOAD_SIZE:
                return False
            else:
                user.user_msg.background_pic = pic
                user.user_msg.save()
                return True
        return False


def info_logged(func):
    def wrapper(request):
        info_log.info('{}[{}]'.format(request.path, request.method))
        decorate_func = func(request)
        return decorate_func
    return wrapper


def login_required(func):
    def wrapper(request,*args, **kwargs):
        info_log.info('{}[{}]'.format(request.path, request.method))
        id = request.session.get('id')
        if id:
            user_id = kwargs.get('user_id', None)
            if user_id:
                if not int(user_id) == int(id):
                    return JsonResponse({'status': False, 'msg': "无权限"})
            decorate_func = func(request, *args, **kwargs)
            return decorate_func
        else:
            return JsonResponse({'status': False, 'msg': "未登录", 'error_code': "1"})
    return wrapper

@info_logged
def login_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': False, 'msg': "请使用post请求"})
    name = request.POST.get('username')
    password = request.POST.get('password')
    user = UserClass(name=name)
    user_obj = user.login(password)
    if user_obj:
        request.session['id'] = user_obj.id
        request.session.set_expiry(60*60)
        return JsonResponse({'status': True, 'msg': "登录成功",
                             'avatar': user_obj.avatar.url,
                             'user_id': user_obj.id,
                             'username': name})
    else:
        return JsonResponse({'status': False, 'msg': "账号或密码错误"})

@info_logged
def email_api(request):
    time = 1
    email = request.POST.get('email', '23')
    if check_email(email):
        title = "你的验证码"
        code = ""
        while time <= 6:
            code += str(random.randint(0, 9))
            time += 1
        body = "你的验证码是:{}".format(code)
        request.session['code'] = code
        t = threading.Thread(target=send_mail(subject=title, message=body, recipient_list=[email], from_email=settings.EMAIL_HOST_USER))
        t.start()
        return JsonResponse({'status': True, 'msg': "发送邮件成功"})
    else:
        return JsonResponse({'status': False, 'msg': "邮箱格式错误"})

@info_logged
def find_pwd_api(request):

    if request.method == 'GET':
        username = request.GET.get('username')
        email = request.GET.get('email')
        try:
            user = UserAll.objects.get(email=email)
        except UserAll.DoesNotExist as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "邮箱未注册"})
        if user.username != username:
            return JsonResponse({'status': False, 'msg': "用户名不存在"})
        else:
            time = 1
            title = "你的验证码"
            code = ""
            while time < 6:
                code += str(random.randint(0, 9))
                time += 1
            body = "你的验证码是:{}".format(code)
            request.session['code1'] = code
            request.session['temp_id'] = user.id
            request.session.set_expiry(5*60)
            send_mail(subject=title, message=body, recipient_list=[email], from_email=settings.EMAIL_HOST_USER)
            return JsonResponse({'status': True, 'msg': "发送邮件成功"})

    if request.method == 'POST':
        code = request.POST.get('code')
        print(code)
        new_pwd = request.POST.get('new_pwd', '12345')
        if code != request.session.get('code1'):
            return JsonResponse({'status': False, 'msg': "验证码错误"})
        else:
            user_id = request.session.get('temp_id')
            user = UserAll.objects.get(id=user_id)
            user.password = hashlib.sha1(new_pwd.encode('utf-8')).hexdigest()
            user.save()
            return JsonResponse({'status': True})

@info_logged
def check_email_code_api(request):
    code = request.POST.get('code', None)
    if request.session.get('code') == code:
        email_access = ''.join(str(uuid.uuid1()).split('-'))
        request.session['email_access'] = email_access
        return JsonResponse({
            'status': True,
            'email_access': email_access,
        })
    else:
        return JsonResponse({'status': False, 'error_code': 3, 'msg': "邮箱验证码错误"})

@info_logged
def register_api(request):

    if request.method == 'GET':
        # 带参数的get
        if request.GET.get('name',None):
            name = request.GET.get('name')
            if UserAll.objects.filter(username=name):
                return JsonResponse({'status': False, 'msg': "用户名已经存在"})
            else:
                return JsonResponse({'status': True, 'msg': ""})
        else:
            tags = Tags.objects.all().values_list('type', flat=True)
            number = tags.count()
            return JsonResponse({
                'total_number': number,
                'tags': list(tags),
            })

    if request.method == 'POST':
        email_access = request.POST.get('email_access')
        if request.session.get('email_access') == email_access and email_access is not None:
            email = request.POST.get('email')
            username = request.POST.get('username')
            password = request.POST.get('password')
            interest = request.POST.getlist('interest')
            birthday = request.POST.get('birthday')
            description = request.POST.get('description')
            gender = request.POST.get('gender', 2)
            try:
                gender = int(gender)
            except Exception as e:
                print(e)
                return JsonResponse({'status': False, 'msg': "性别格式错误"})
            if not gender in [0, 1, 2]:
                return JsonResponse({'status': False, 'msg': "性别格式错误"})
            new_user = UserClassForProject(name=username)

            if birthday:
                if not re.match(r'(\w+){3,4}-(\w+){2}-(\w+){2}', birthday):
                    return JsonResponse({'status': False, 'msg': "生日格式错误"})

            if UserAll.objects.filter(email=email):
                return JsonResponse({'status': False, 'msg': "邮箱已经存在", 'error_code': 3})

            if not new_user.check_uniqueness_name():
                return JsonResponse({'status': False, 'msg': "用户名已存在", 'error_code': 3})

            if new_user.create_user(password, email, interest, description, birthday, gender):
                return JsonResponse({'status': True, 'msg': "创建用户成功"})
            else:
                return JsonResponse({'status': False, 'error_code': 3, 'msg': "密码不能为空"})
        else:
            return JsonResponse({'status': False, 'error_code': 1, 'msg': "无权限"})

@info_logged
def logout_api(request):
    if request.method == 'POST':
        try:
            id = int(request.POST.get('id', 0))
        except Exception as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "id格式错误"})
        if int(request.session.get('id')) == id:
            request.session.delete('id')
            return JsonResponse({'status': True, 'msg': "退出登录成功"})
        else:
            return JsonResponse({'status': False, 'error_code': 1, 'msg': "无权限"})
    else:
        return JsonResponse({'status': False, 'msg': "请使用post方法"})


@login_required
def floor_comment_info_api(request, user_id):
    user_id = int(user_id)
    floor_comment_info = []
    post_floor = PostFloor.objects.select_related('user').filter(post__writer_id=user_id, display_status=True)
    post_floor_number = post_floor.count()
    for floor in post_floor:
        # 自己盖的楼层不提示消息
        if floor.user_id == user_id:
            continue
        floor_comment_info.append({
            'id': floor.id,
            'post_content': floor.post.content,
            'post_id': floor.post_id,
            'writer_id': floor.user_id,
            'writer_name': floor.user.username,
            'writer_avatar': floor.user.avatar.url,
            'read_status': floor.read_status,
            'time': str(floor.create_time),
            'floor_number': floor.floor_number,
            'floor_content': floor.content,
        })
    post_floor.update(read_status=True)
    return JsonResponse({
        'user_id': user_id,
        'floor_comment_number': post_floor_number,
        'floor_comment_info': floor_comment_info,
    })


@login_required
def comment_info_api(request, user_id):
    user_id = int(user_id)
    comment_info = []
    user_comment_ids = list(FloorComments.objects.filter(user_id=user_id, status=True).values_list('id', flat=True))
    # 自己评论自己不在消息提醒里
    replies = FloorComments.objects.filter((Q(replied_comment__in=user_comment_ids)| Q(reply__user_id=user_id))& Q(display_status=True)).exclude(user_id=user_id).select_related('user', 'reply__user', 'reply')
    comment_info_number = replies.count()
    for a_reply in replies:
        if a_reply.reply.user_id==user_id:
            floor_reply_status = True
            replied_content = a_reply.reply.content
        else:
            floor_reply_status = False
            replied_content = FloorComments.objects.filter(id=a_reply.replied_comment, status=True).values_list('content')[0]
        comment_info.append({
            'id': a_reply.id,
            'comment_user_id': a_reply.user_id,
            'comment_user_name': a_reply.user.username,
            'comment_user_avatar': a_reply.user.avatar.url,
            'content': a_reply.content,
            'time': str(a_reply.create_time),
            'post_id': a_reply.reply.post_id,
            'comment_floor': a_reply.reply.floor_number,
            'floor_reply_status': floor_reply_status,
            'replied_content': replied_content,
            'read_status': a_reply.read_status,
        })
    replies.update(read_status=True)
    return JsonResponse({
        'user_id': user_id,
        'comment_info_number': comment_info_number,
        'comment_info': comment_info,
    })


@login_required
def delete_comment_api(request, user_id):
    user_id = int(user_id)
    delete_id = request.DELETE.get('comment_id', 0)
    try:
        delete_id = int(delete_id)
    except Exception as e:
        info_log.info(e)
        return JsonResponse({'status': False, 'msg': "id格式错误"})
    comment = FloorComments.objects.filter(id=delete_id)
    if comment:
        comment = comment[0]
        if comment.user_id == user_id:
            if comment.replied_comment == 0:
                FloorComments.objects.filter(replied_comment=comment.id).delete()
            comment.delete()
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False, 'msg': "无权限", 'error_code': 1})
    else:
        return JsonResponse({'status': False, 'msg': "id不存在", 'error_code': 3})


@login_required
def delete_info_api(request, user_id):
    if not request.method == 'DELETE':
        return JsonResponse({'status': False})
    user_id = int(user_id)
    type = request.DELETE.get('type')
    if type == 'praise':
        praise_id = request.DELETE.getlist('praise_id')
        for a_id in praise_id:
            UserPraise.objects.filter(id=a_id).update(info_status=False)
    elif type == 'comment':
        comment_id = request.DELETE.getlist('comment_id')
        for a_id in comment_id:
            FloorComments.objects.filter(id=a_id).update(display_status=False)
    elif type == 'floor':
        floor_id = request.DELETE.getlist('floor_id')
        for a_id in floor_id:
            PostFloor.objects.filter(id=a_id).update(display_status=False)
    else:
        return JsonResponse({'status': False, 'error_code': 2, 'msg': "类型错误"})
    return JsonResponse({'status': True})


@login_required
def praise_info_api(request, user_id):
    user_id = int(user_id)
    praise_info = []
    praise_number = 0
    post_ids = list(Post.objects.filter(writer_id=user_id).values_list('id', flat=True))
    for post_id in post_ids:
        # 自己点赞自己不会在消息里
        user_praises = UserPraise.objects.filter(Q(post_id=post_id)& Q(display_status=True)&Q(info_status=True)).exclude(user__user_id=user_id).select_related('post', 'user__user')
        if user_praises:
            for praise in user_praises:
                praise_number += 1
                praise_info.append({
                    'info_id': praise.id,
                    'read_status': praise.read_status,
                    'person_id': praise.user.user_id,
                    'person_avatar': praise.user.user.avatar.url,
                    'person_name': praise.user.user.username,
                    'post_id': post_id,
                    'post_content': praise.post.content,
                })
            user_praises.update(read_status=True)
        else:
            continue
    return JsonResponse({
        'user_id': user_id,
        'praise_info_number': praise_number,
        'praise_info': praise_info,
    })


@login_required
def watching_bar_api(request, user_id):
    user_id = int(user_id)
    if request.method == 'DELETE':
        bar_id = request.DELETE.get('bar_id')
        temp = UserWatching.objects.filter(bar_id=bar_id, user__user_id=user_id).update(display_status=False, info_status=False)
        if temp:
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False, 'msg': "不存在"})
    if request.method == 'GET':
        bar_msg = []
        user_watching = UserWatching.objects.select_related('bar').filter(user__user_id=user_id, display_status=True)
        number = user_watching.count()
        for i in user_watching:
            bar_msg.append({
                'bar_id': i.bar.id,
                'bar_name': i.bar.name,
                'bar_tags': [x for x in i.bar.feature.values_list('type', flat=True)],
                'bar_icon': i.bar.photo.url,
            })
        return JsonResponse({
            'user_id': user_id,
            'total_number': number,
            'bar_msg': bar_msg,
        })
    if request.method == 'POST':
        bar_id = request.POST.get('bar_id')
        if not PostBars.objects.filter(id=bar_id):
            return JsonResponse({'status': False, 'msg': "不存在"})
        user_msg_id = UserAll.objects.get(id=user_id).user_msg.id
        UserWatching.objects.update_or_create(user_id=user_msg_id, bar_id=bar_id, defaults={'display_status':True})
        return JsonResponse({'status': True})


@login_required
def msg_api(request, user_id):
    user_id = int(user_id)
    if request.method == 'DELETE':
        type = request.DELETE.get('type')
        if type == 'watching':
            watching_ids = request.DELETE.getlist('watching_ids')
            for i in watching_ids:
                UserWatching.objects.filter(id=i).update(info_status=False)
        elif type == 'following':
            following_ids = request.DELETE.getlist('following_ids')
            for i in following_ids:
                UserFollow.objects.filter(id=i).update(info_status=False)
        else:
            return JsonResponse({'status': False, 'msg': '类型错误', 'error_code': 2})
        return JsonResponse({'status': True})
    if request.method == 'GET':
        new_follower = []
        new_watcher = []
        follower_update_ids = []
        followers = UserFollow.objects.select_related('user').filter(follower_id=int(user_id), display_status=True, info_status=True)
        new_follower_number = followers.count()
        for follower in followers:
            person = follower.user.user
            follower_update_ids.append(follower.id)
            new_follower.append({
                'id': follower.id,
                'user': person.id,
                'avatar': person.avatar.url,
                'username': person.username,
                'read_status': follower.read_status,
            })
        UserFollow.objects.filter(id__in=follower_update_ids).update(read_status=True)

        watcher_update_ids = []
        bar_ids = PostBars.objects.filter(master_id=user_id).values_list('id', flat=True)
        watchers = UserWatching.objects.filter(bar_id__in=bar_ids, display_status=True, info_status=True).select_related('user', 'user__user')[0:10]
        new_watcher_number = watchers.count()
        for watcher in watchers:
            person = watcher.user
            watcher_update_ids.append(watcher.id)
            new_watcher.append({
                'id': watcher.id,
                'user': person.user_id,
                'avatar': person.user.avatar.url,
                'username': person.user.username,
                'read_status': watcher.read_status,
            })
        UserWatching.objects.filter(id__in=watcher_update_ids).update(read_status=True)

        return JsonResponse({
            'user_id': user_id,
            'number': new_follower_number + new_watcher_number,
            'new_follower_number': new_follower_number,
            'new_follower': new_follower,
            'new_watcher_number': new_watcher_number,
            'new_watcher': new_watcher,
        })


@login_required
def user_concern_api(request, user_id):
    user_id = int(user_id)
    if request.method == 'DELETE':
        delete_id = request.DELETE.get('user_id')
        temp = UserFollow.objects.filter(user__user_id=user_id, follower_id=delete_id)
        if temp:
            temp.update(display_status=False, mutual_following=False, info_status=False)
            UserFollow.objects.filter(user__user_id=delete_id, follower_id=user_id).update(mutual_following=False)
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False, 'msg': "不存在"})
    if request.method == 'GET':
        concern = []
        user_follows= UserFollow.objects.select_related('follower').filter(user__user_id=user_id, display_status=True)
        concern_number = user_follows.count()
        for user_follow in user_follows:
            concern.append({
                'user_id': user_follow.follower_id,
                'user_avatar': user_follow.follower.avatar.url,
                'user_name': user_follow.follower.username,
                'follower_status': user_follow.mutual_following
            })
        return JsonResponse({
            'user_id': user_id,
            'concern_number': concern_number,
            'concern': concern,
        })
    # 相互关注记得修改
    if request.method == 'POST':
        concern_id = request.POST.get('user_id')
        if not UserAll.objects.filter(id=concern_id):
            return JsonResponse({'status': False, 'msg': "用户不存在"})
        else:
            # 别人关注了我
            temp = UserFollow.objects.filter(Q(user__user_id=concern_id) & Q(follower_id=user_id) & Q(display_status=True))
            if temp:
                flag = True
                temp.update(mutual_following=True)
            else:
                flag = False
            user_msg_id = UserAll.objects.get(id=user_id).user_msg.id
            new_follower = UserFollow.objects.update_or_create(follower_id=concern_id, user_id=user_msg_id,
                                                               defaults={'mutual_following': flag, 'display_status': True})
            return JsonResponse({'status': True})


@login_required
def user_follower_api(request, user_id):
    user_id = int(user_id)
    user_followers = UserFollow.objects.select_related('user__user').filter(follower_id=user_id, display_status=True)
    follower_number = user_followers.count()
    follower = []
    for user_follower in user_followers:
        follower.append({
            'follower_id': user_follower.user.user_id,
            'follower_avatar': user_follower.user.user.avatar.url,
            'follower_name': user_follower.user.user.username,
            'concern_status': user_follower.mutual_following,
        })
    return JsonResponse({
        'user_id': user_id,
        'follower_number': follower_number,
        'follower': follower,
    })


@login_required
def user_collection_api(request, user_id):
    user_id = int(user_id)
    try:
        user = UserDetailMsg.objects.get(user_id=user_id)
    except Exception as e:
        info_log.info(e)
        return JsonResponse({'status': False, 'msg': "不存在"})
    if request.method == 'DELETE':
        post_id = request.DELETE.get('post_id')
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist as e:
            info_log.info(e)
            return JsonResponse({'status': False, 'msg': "收藏不存在"})
        user.collections.remove(post)
        user.save()
        return JsonResponse({'status': True})
    if request.method == 'GET':
        collections = []
        collection_number = 0
        for i in user.collections.all().select_related('writer'):
            collection_number += 1
            collections.append({
                'id': i.id,
                'master_avatar': i.writer.avatar.url,
                'master_name': i.writer.username,
                'master_id': i.writer_id,
                'post_id': i.id,
                'post_title': i.title,
                'post_content': i.content,
                'post_pics': ["/"+x for x in PostPhotos.objects.filter(post_id=i.id).values_list('pic', flat=True)]
            })
        return JsonResponse({
            'user_id': user_id,
            'collection_number': collection_number,
            'collections': collections
        })
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        try:
            post = Post.objects.get(id=post_id)
        except Exception as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "帖子不存在"})
        if user.collections.filter(id=post.id):
            return JsonResponse({'status': False, 'msg': "收藏过了", 'error_code':3})
        else:
            user.collections.add(post)
            user.save()
        return JsonResponse({'status': True})


# @login_required
def personal_center_api(request, user_id):
    logged_id = request.session.get('id', None)
    if not logged_id:
        return JsonResponse({'status': False, 'msg': "未登录"})
    user_id = int(user_id)
    try:
        user = UserAll.objects.get(id=user_id)
    except UserAll.DoesNotExist as e:
        info_log.warning(e)
        return JsonResponse({'status': False, 'msg': "用户不存在"})
    else:
        if request.method == 'GET':
            type = request.GET.get('type')
            if type and type == 'message':
                if logged_id != user_id:
                    return JsonResponse({'status': False, 'msg': "无权限"})
                ids = FloorComments.objects.exclude(replied_comment=0).values_list('id', flat=True)
                return JsonResponse({
                    'floor_message': PostFloor.objects.filter(Q(post__writer_id=user_id)& Q(read_status=False) & Q(display_status=True)).only('post__writer_id').exclude(user_id=user_id).count(),
                    'reply_message': FloorComments.objects.filter(Q(user_id=user_id) & Q(id__in=ids)&Q(read_status=False) & Q(display_status=True)).exclude(user_id=user_id).count(),
                    'praise_message': UserPraise.objects.filter(Q(post__writer_id=user_id) & Q(read_status=False) & Q(info_status=True)).exclude(user__user_id=user_id).only('post__writer_id').count(),
                    'follower_message': UserFollow.objects.filter(Q(follower_id=user_id) & Q( read_status=False) & Q(info_status=True)).count(),
                })
            if user_id == logged_id:
                follow_status = None
            else:
                follow_status = bool(UserFollow.objects.filter(user__user_id=logged_id, follower=user))
            birthday = user.user_msg.birthday
            if birthday is None:
                birthday = None
            else:
                birthday = str(birthday)
            return JsonResponse({
                'user_id': user_id,
                'username': user.username,
                'gender': user.user_msg.gender,
                'description': user.user_msg.description,
                'birthday': birthday,
                'avatar': user.avatar.url,
                'follower_number': UserFollow.objects.filter(follower=user, display_status=True).count(),
                'collection_number': user.user_msg.collections.count(),
                'concern_number': UserFollow.objects.filter(user__user=user, display_status=True).count(),
                'watched_bar_number': user.user_msg.watching.filter(userwatching__display_status=True).count(),
                'background_pic': user.user_msg.background_pic.url,
                'interests': [x.type for x in user.user_msg.interest.all()],
                'posts': user.post_writer.filter(display_status=True).count(),
                'follow_status': follow_status,
            })
        # 修改个人信息
        if request.method == 'POST':
            username = request.POST.get('username', None)
            description = request.POST.get('description', None)
            gender = request.POST.get('gender')
            birthday = request.POST.get('birthday', None)
            interests = request.POST.getlist('interests', None)
            if UserAll.objects.exclude(id=user_id).filter(username=username):
                return JsonResponse({'status': False, 'msg': "用户名已经存在"})
            else:
                if username:
                    user.username = username
            if description:
                user.user_msg.description = description
            if gender:
                try:
                    gender = int(gender)
                except Exception as e:
                    info_log.warning(e)
                    return JsonResponse({'status': False, 'msg': "性别格式错误"})
                if gender in [0, 1, 2]:
                    user.user_msg.gender = gender
            if birthday and re.match(r'(\w+){3,4}-(\w+){2}-(\w+){2}', birthday):
                user.user_msg.birthday = birthday
            if interests:
                for x in user.user_msg.interest.all():
                    user.user_msg.interest.remove(x)
                for i in interests:
                    try:
                        user.user_msg.interest.add(Tags.objects.get(type=i))
                    except Exception as e:
                        info_log.warning(e)
                        continue
            user.save()
            user.user_msg.save()
            return JsonResponse({'status': True})


@login_required
def pwd_reset(request, user_id):
    user_id = int(user_id)
    old_pwd = request.POST.get('old_pwd')
    new_pwd = request.POST.get('new_pwd')
    a_user = UserClass(id=user_id)
    if a_user.revise_pwd(old_pwd, new_pwd):
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status': False, 'msg': "原密码错误"})


@login_required
def upload_photo(request):
    try:
        user_id = int(request.POST.get('user_id'))
    except Exception as e:
        print(e)
        return JsonResponse({'status': False, 'msg': "id格式错误"})
    if int(request.session.get('id')) != user_id:
        return JsonResponse({'status': False, 'msg': "无权限"})
    type = request.POST.get('type')
    user = UserClassForProject(id=user_id)
    if not user.check_user():
        return JsonResponse({'status': False, 'msg': "用户不存在"})
    else:
        if type == 'avatar':
            if user.upload_avatar(request):
                url = UserAll.objects.get(id=user_id).avatar.url
                return JsonResponse({'status': True, 'pic': url})
            else:
                return JsonResponse({'status': False, 'msg': "图片格式错误或太大了"})
        elif type == 'background':
            if user.upload_background(request):
                url = UserDetailMsg.objects.get(user_id=user_id).background_pic.url
                return JsonResponse({'status': True, 'pic': url})
            else:
                return JsonResponse({'status': False, 'msg': "图片格式错误或太大了"})
        else:
            return JsonResponse({'status': False, 'msg': "指定类型不存在"})


@login_required
def search_api(request):
    user_id =request.session.get('id')
    output = []
    type = request.GET.get('type', 'post')
    search = request.GET.get('search')
    if not search:
        return JsonResponse({'status': False, 'msg': "请指定查找内容"})
    if type == 'bar':
        bars = PostBars.objects.filter(name__icontains=search)
        for bar in bars:
            output.append({
                'bar_id': bar.id,
                'bar_title': bar.name,
                'bar_description': bar.short_description,
                'bar_icon': bar.photo.url,
                'post_number': bar.bar_number,
                'watching_number': UserWatching.objects.filter(bar_id=bar.id, display_status=True).count(),
                'watching_status': bool(UserWatching.objects.filter(user__user_id=user_id, display_status=True)),
            })
        return JsonResponse({
            'bar_number': bars.count(),
            'bar_msg': output,
        })
    elif type == 'post':
        posts = Post.objects.select_related('writer', 'bar').filter(title__icontains=search, display_status=True)
        for post in posts:
            pics = PostPhotos.objects.filter(post_id=post.id)
            if pics:
                photo_url = pics[0].pic.url
            else:
                photo_url = None
            output.append({
                'post_id': post.id,
                'post_writer_id': post.writer_id,
                'post_writer_name': post.writer.username,
                'post_writer_avatar': post.writer.avatar.url,
                'post_content': post.content,
                'bar_name': post.bar.name,
                'post_photo': photo_url,
                'comment_number': PostFloor.objects.filter(post_id=post.id, unfold_status=True).count()-1,
                'praise_number': UserPraise.objects.filter(post_id=post.id, display_status=True).count(),
            })
        return JsonResponse({
            'post_number': posts.count(),
            'post_msg': output,
        })
    elif type == 'user':
        users = UserAll.objects.filter(username__icontains=search)
        for user in users:
            output.append({
                'user_id': user.id,
                'user_avatar': user.avatar.url,
                'user_name': user.username,
                'user_followers': UserFollow.objects.filter(follower_id=user.id, display_status=True).count(),
            })
        return JsonResponse({
            'user_number': users.count(),
            'user_msg': output,
        })
    else:
        return JsonResponse({'status': False, 'msg': "类型指定错误"})


@login_required
def floor_msg_api(request, post_id):
    post_id = int(post_id)
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist as e:
        print(e)
        return JsonResponse({'status': False, 'msg': "不存在"})
    else:
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            if not int(request.session.get('id')) == int(user_id):
                return JsonResponse({'status': False, 'msg': "无权限"})
            reply_id = request.POST.get('reply_id', 0)
            reply_floor = request.POST.get('reply_floor')
            print(reply_floor)
            try:
                reply_floor = int(reply_floor)
                reply_id = int(reply_id)
            except Exception as e:
                info_log.warning(e)
                return JsonResponse({'status':False, 'msg': "数据格式错误"})
            # 敏感词过滤
            gfw = DFAFilter()
            gfw.database_parse()
            content = request.POST.get('content')
            content = gfw.filter(content)
            user = UserAll.objects.get(id=user_id)
            if reply_floor == 1:
                PostFloor.objects.create(post=post, user=user, content=content)
                return JsonResponse({'status': True, 'msg': "建楼成功"})
            floor = PostFloor.objects.filter(post=post, floor_number=reply_floor)
            if floor:
                floor = floor[0]
                if reply_id != 0:
                    if not FloorComments.objects.filter(id=reply_id):
                        return JsonResponse({'status': False, 'msg': "评论不存在"})
                FloorComments(reply=floor, user=user, content=content, replied_comment=reply_id).save()
                return JsonResponse({'status': True})
            else:
                return JsonResponse({'status': False, 'msg': "楼不存在"})
        if request.method == 'GET':
            floor = request.GET.get('floor')
            # 指定检索楼层
            if floor:
                post_floor = PostFloor.objects.filter(post=post, floor_number=floor, unfold_status=True)
                if not post_floor:
                    return JsonResponse({'status': False, 'msg': "不存在"})
                else:
                    comment_msg = []
                    post_floor = post_floor[0]
                    comments = FloorComments.objects.select_related('user').filter(Q(reply_id=post_floor.id) & Q(status=True))
                    for comment in comments:
                        if bool(comment.replied_comment):
                            temp = FloorComments.objects.get(id=comment.replied_comment)
                            reply_person_id = temp.user_id
                            reply_person_name = temp.user.username
                        else:
                            reply_person_id = None
                            reply_person_name = None
                        comment_msg.append({
                            'comment_id': comment.id,
                            'reply_status': bool(comment.replied_comment),
                            'reply_person_name': reply_person_name,
                            'reply_person_id': reply_person_id,
                            'person_id': comment.user_id,
                            'person_name': comment.user.username,
                            'person_avatar': comment.user.avatar.url,
                            'datetime': str(comment.create_time),
                            'content': comment.content,
                        })
                    return JsonResponse({
                        'status': True,
                        'floor_number': floor,
                        'floor_content': post_floor.content,
                        'floor_writer_id': post_floor.user_id,
                        'floor_writer_name': post_floor.user.username,
                        'floor_writer_avatar': post_floor.user.avatar.url,
                        'comment_number': comments.count(),
                        'comment_msg': comment_msg,
                    })
            else:
                floor_info = []
                page = request.GET.get('page', 1)
                post_floor = PostFloor.objects.select_related('user').filter(post=post, unfold_status=True).exclude(floor_number=1)
                paginator = Paginator(post_floor, 5)
                num_page = paginator.num_pages
                try:
                    current_page = paginator.page(page)
                    limited_floors = current_page.object_list
                except PageNotAnInteger:
                    current_page = paginator.page(1)
                    limited_floors = current_page.object_list
                except EmptyPage:
                    current_page = paginator.page(1)
                    limited_floors = current_page.object_list
                for i in limited_floors:
                    floor_info.append({
                        'floor': i.floor_number,
                        'person_id': i.user_id,
                        'person_name': i.user.username,
                        'person_avatar': i.user.avatar.url,
                        'datetime': i.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'content': i.content,
                    })
                return JsonResponse({
                    'floor_number': post_floor.count(),
                    'total_page': num_page,
                    'per_page': 5,
                    'current_page': current_page.number,
                    'number': len(limited_floors),
                    'floor_info': floor_info,
                })


@login_required
def post_msg_api(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist as e:
        print(e)
        return JsonResponse({'status': False, 'msg': "不存在"})
    else:
        if not post.display_status:
            return JsonResponse({'status': False, 'msg': "不存在"})
        user_id = request.session.get('id')
        post_msg = {
            'person_id': post.writer_id,
            'person_name': post.writer.username,
            'person_avatar': post.writer.avatar.url,
            'follow_status': bool(UserFollow.objects.filter(user__user_id=user_id, follower_id=post.writer_id, display_status=True)),
            'time': str(post.create_time),
            'pic': list(PostPhotos.objects.filter(post_id=post_id).values_list('pic', flat=True)),
            'content': post.content,
            'bar_id': post.bar_id,
            'bar': post.bar.name,
        }
        return JsonResponse({
            'status': True,
            'user_id': user_id,
            'collection_status': bool(UserAll.objects.get(id=user_id).user_msg.collections.filter(id=post_id)),
            'praise_status': bool(UserPraise.objects.filter(user__user_id=user_id, display_status=True, post_id=post_id)),
            'post_msg': post_msg,
        })


@login_required
def praise_api(request):

    if request.method == 'DELETE':
        user_id = request.DELETE.get('user_id')
        try:
            user_id = int(user_id)
        except Exception as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "格式错误"})
        if user_id != request.session.get('id'):
            return JsonResponse({'status': False, 'msg': "无权限"})
        post_id = request.DELETE.get('post_id')
        try:
            post_id = int(post_id)
        except Exception as e:
            info_log.warning(e)
            return JsonResponse({'status': False, 'msg': "格式错误"})
        path = os.path.join(settings.BASE_LOG_DIR, 'tmp.txt')
        fp = open(path, 'a+')
        fp.write("user_id:{}---post_id:{} \n".format(user_id, post_id))
        temp = UserPraise.objects.filter(Q(post_id=post_id)& Q(user__user_id=user_id)).update(display_status=False)
        fp.write(str(temp))
        fp.close()
        if temp != 0:
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False, 'msg': "不存在"})
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user_id = int(user_id)
        except Exception as e:
            info_log.warning(e)
            return JsonResponse({'status': False, 'msg': "格式错误"})
        if user_id != request.session.get('id'):
            return JsonResponse({'status': False, 'msg': "无权限"})
        post_id = request.POST.get('post_id')
        if not Post.objects.filter(id=post_id, display_status=True):
            return JsonResponse({'status': False, 'msg': "帖子不存在"})
        user_msg_id = UserAll.objects.get(id=user_id).user_msg.id
        UserPraise.objects.update_or_create(post_id=post_id, user_id=user_msg_id, defaults={'display_status': True})
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status':False, 'msg':"请使用delete和post"})


class PicThread(threading.Thread):
    def __init__(self, name, pic, post_id):
        self.pic = pic
        self.post_id = post_id
        super(PicThread, self).__init__(name=name)

    def run(self) -> None:
        print(threading.current_thread().name, "is running to save a pic")
        try:
            PostPhotos.objects.create(post_id=self.post_id, pic=self.pic)
        except Exception as e:
            print(e)


@login_required
def home_api(request):
    person_id = request.session.get('id')
    person = UserAll.objects.get(id=person_id)
    if request.method == 'GET':
        post_msg = []
        user_id = request.GET.get('user')
        lastId = request.GET.get('lastId', 0)
        # page = request.GET.get('page', 1)
        if user_id:
            posts = Post.objects.filter(writer_id=user_id, display_status=True)
        else:
            interests = person.user_msg.interest.all()
            posts1 = Post.objects.filter(bar__feature__in=interests, display_status=True)
            if posts1.count() >= 21:
                posts = posts1.order_by('-create_time')
            else:
                ids = list(UserPraise.objects.annotate(count=Count('post')).order_by('-count').values_list('post', flat=True))
                info_log.info(ids)
                posts2 = Post.objects.filter(id__in=ids, display_status=True)
                posts = (posts1 | posts2).distinct()
        info_log.info(posts)
        try:
            paginator = PaginatorThroughLast(posts, 7, lastId=lastId)
            num_page = paginator.total_page()
            limited_posts = paginator.page()
        except IDNotInteger as e:
            info_log.info(e)
            return JsonResponse({'status': False, 'msg': "id无法转成整数"})
        temp = list(limited_posts)
        if temp:
            lastId = temp[-1].id
        else:
            lastId = 0
        for i in limited_posts:
            pics = ["/media/"+x for x in PostPhotos.objects.filter(post_id=i.id).values_list('pic', flat=True)]
            info = {
                'post_id': i.id,
                'post_pic': pics,
                'post_content': i.content,
                'comment_number': PostFloor.objects.filter(post_id=i.id, unfold_status=True).count() - 1,
                'praise_number': UserPraise.objects.filter(post_id=i.id, display_status=True).count(),
                'bar_id': i.bar_id,
                'bar_name': i.bar.name,
                'bar_tags': list(i.bar.feature.values_list('type', flat=True)),
                'writer_id':i.writer_id,
                'writer_name':i.writer.username,
                'writer_avatar': i.writer.avatar.url,
                'praise_status': bool(UserPraise.objects.filter(display_status=True, user__user=person, post_id=i.id))
            }
            post_msg.append(info)
        return JsonResponse({
            'lastId': lastId,
            'total_page': num_page,
            'this_page': len(limited_posts),
            'per_page': 7,
            'post_msg': post_msg,
        })

    if request.method == 'POST':
        user_id = request.POST.get('user_id', 0)
        bar_id = request.POST.get('bar_id', 0)
        title = request.POST.get('title', "无标题")
        content = request.POST.get('content')
        pics = request.FILES.getlist('pic')
        if request.session.get('id', None) != int(user_id):
            return JsonResponse({'status': False, 'msg': "无权限"})
        else:
            if not PostBars.objects.filter(id=bar_id):
                return JsonResponse({'status': False, 'msg': "帖子不存在"})
            # 多线程写入图片
            new_post = Post(writer_id=user_id, bar_id=bar_id, title=title, content=content)
            new_post.save()
            post_id = new_post.id
            thread_lists = []
            i = 0
            for pic in pics:
                i+=1
                t = PicThread(name='Thread_{}'.format(i), post_id=post_id, pic=pic)
                thread_lists.append(t)
            for t in thread_lists:
                t.setDaemon(True)
                t.start()
            # 都开始再同步
            for t in thread_lists:
                t.join()
            return JsonResponse({'status': True})

    if request.method == 'DELETE':
        user_id = request.DELETE.get('user_id')
        post_id = request.DELETE.get('post_id')
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "帖子不存在"})
        else:
            if post.writer_id != int(user_id):
                return JsonResponse({'status': False, 'msg': "无权限"})
            else:
                post.display_status = False
                FloorComments.objects.filter(reply__post_id=post_id).update(display_status=False)
                post.save()
                return JsonResponse({'status': True})


@login_required
def post_bar_api(request):
    user_id = request.session.get('id')
    if request.GET.get('bar_id'):
        bar_id = request.GET.get('bar_id')
        try:
            bar = PostBars.objects.get(id=bar_id)
        except PostBars.DoesNotExist as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "id不存在"})
        else:
            post_info = []
            posts = Post.objects.filter(bar_id=bar_id, display_status=True).select_related('writer')
            for i in posts:
                post_info.append({
                    'writer_id': i.writer_id,
                    'writer_avatar': i.writer.avatar.url,
                    'writer_name': i.writer.username,
                    'post_id': i.id,
                    'post_content': i.content,
                    'post_pic': ["/media/"+x for x in PostPhotos.objects.filter(post_id=i.id).values_list('pic', flat=True)],
                    'comment_number': PostFloor.objects.filter(post_id=i.id, unfold_status=True).count() - 1, # 减去1楼
                    'praise_number': UserPraise.objects.filter(post_id=i.id, display_status=True).count(),
                    'time': str(i.create_time),
                })
            return JsonResponse({
                'status': True,
                'bar_id': bar.id,
                'name': bar.name,
                'icon': bar.photo.url,
                'watcher_number': UserWatching.objects.filter(bar_id=bar.id, display_status=True).count(),
                'post_number': bar.bar_number,
                'description': bar.short_description,
                'watching_status': bool(UserWatching.objects.filter(user__user_id=user_id, bar_id=bar_id, display_status=True)),
                'post_info': post_info,
            })
    elif request.GET.get('bar_tag'):
        bar_info = []
        bar_tag = request.GET.get('bar_tag')
        bars = PostBars.objects.filter(feature__type__contains=bar_tag)
        for bar in bars:
            bar_info.append({
                'bar_id': bar.id,
                'name': bar.name,
                'icon': bar.photo.url,
                'post_number': bar.bar_number,
                'description': bar.short_description,
                'watching_status': bool(UserWatching.objects.filter(user__user_id=user_id, bar_id=bar.id, display_status=True))
            })
        return JsonResponse({
            'status': True,
            'search_tag': bar_tag,
            'number': bars.count(),
            'bar_info': bar_info,
        })
    else:
        return JsonResponse({'status': False, 'msg':"请至少带上bar_id和bar_tag中的一个"})



