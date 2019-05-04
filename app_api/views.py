from django.shortcuts import render, HttpResponse
from MyTieba import settings
from django.db.models import Max, Avg, F, Q, Min, Count, Sum
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from app_api.models import *
import json
import re
import hashlib
import random


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
        if re.match(r'^\w+$', name):
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
        pic = request.FILE.get('pic')
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

    def create_user(self, password, email, interest):
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
            user_msg.save()
            return True
        else:
            return False

    def upload_background(self, request):
        user = UserAll.objects.get(id=self.id)
        pic = request.FILE.get('pic')
        suffix = os.path.splitext(pic.name)[1]
        if not suffix:
            return False
        if suffix.lower() == '.jpeg' or suffix.lower() == ".png" or suffix.lower() == ".jpg":
            if pic._size > settings.MAX_UPLOAD_SIZE:
                return False
            else:
                user.user_msg.background_pic = pic
                user.save()
                return True
        return False


def login_required(func):
    def wrapper(request,*args, **kwargs):
        id = request.session.get('id')
        if id:
            decorate_func = func(request, *args, **kwargs)
            return decorate_func
        else:
            return JsonResponse({'status': False, 'msg': "未登录", 'error_code': "无权限"})
    return wrapper


def login_api(request):
    name = request.POST.get('username')
    password = request.POST.get('password')
    user = UserClass(name=name)
    user_obj = user.login(password)
    if user_obj:
        request.session['id'] = user_obj.id
        return JsonResponse({'status': True, 'msg': "登录成功",
                             'avatar': user_obj.avatar.url,
                             'user_id': user_obj.id,
                             'username': name})
    else:
        return JsonResponse({'status': False, 'msg': "账号或密码错误"})


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
        print(body)
        request.session['code'] = code
        send_mail(subject=title, message=body, recipient_list=[email], from_email=settings.EMAIL_HOST_USER)
        return JsonResponse({'status': True, 'msg': "发送邮件成功"})
    else:
        return JsonResponse({'status': False})


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
            new_user = UserClassForProject(name=username)

            if UserAll.objects.filter(email=email):
                return JsonResponse({'status': False, 'msg': "邮箱已经存在", 'error_code': 3})

            if not new_user.check_uniqueness_name():
                return JsonResponse({'status': False, 'msg': "用户名已存在", 'error_code': 3})

            if new_user.create_user(password, email, interest):
                return JsonResponse({'status': True, 'msg': "创建用户成功"})
            else:
                return JsonResponse({'status': False, 'error_code': 3, 'msg': "密码不能为空"})

        else:
            return JsonResponse({'status': False, 'error_code': 1, 'msg': "无权限"})


def logout_api(request):
    if request.method == 'POST':
        if int(request.session.get('id')) == int(request.POST.get('id')):
            request.session.delete('id')
            return JsonResponse({'status': True, 'msg': "退出登录成功"})
        else:
            return JsonResponse({'status': False, 'error_code': 1, 'msg': "无权限"})
    else:
        return JsonResponse({'status': False, 'msg': "请使用post方法"})


def floor_comment_info_api(request, user_id):

    floor_comment_info = []
    post_floor = PostFloor.objects.select_related('user').filter(post__bar__master_id=user_id, unfold_status=False)
    post_floor_number = post_floor.count()
    for floor in post_floor:
        floor_comment_info.append({
            'id': floor.id,
            'post_content': floor.content,
            'post_id': floor.post_id,
            'writer_id': floor.user_id,
            'writer_name': floor.user.username,
            'writer_avatar': floor.user.avatar.url,
            'read_status': floor.read_status,
        })
    post_floor.update(read_status=True)
    return JsonResponse({
        'user_id': user_id,
        'floor_comment_number': post_floor_number,
        'floor_comment_info': floor_comment_info,
    })


def comment_info_api(request, user_id):
    comment_info = []
    user_comment_ids = list(FloorComments.objects.filter(user_id=user_id, status=True).value_list('id', flat=True))
    replies = FloorComments.objects.filter(replied_comment__in=user_comment_ids, status=True).select_related('user', 'reply')
    comment_info_number = replies.cout()
    for a_reply in replies:
        comment_info.append({
            'id': a_reply.id,
            'comment_user_id': a_reply.user_id,
            'comment_user_name': a_reply.user.username,
            'comment_user_avatar': a_reply.user.avatar.url,
            'content': a_reply.content,
            'time': str(a_reply.create_time),
            'post_id': a_reply.reply.post_id,
            'comment_floor': a_reply.reply.floor_number,
            'reply_status': bool(a_reply.user_id==user_id),
            'read_status': a_reply.read_status,
        })
    replies.update(read_status=True)
    return JsonResponse({
        'user_id': user_id,
        'comment_info_number': comment_info_number,
        'comment_info': comment_info,
    })


def delete_comment_api(request, user_id):
    delete_id = request.DELETE.get('comment_id', 0)
    comment = FloorComments.objects.filter(id=delete_id)
    if comment:
        comment = comment[0]
        if comment.user_id == int(user_id):
            if comment.replied_comment == 0:
                FloorComments.objects.filter(id=comment.replied_comment).delete()
            comment.delete()
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False, 'msg': "无权限", 'error_code': 1})
    else:
        return JsonResponse({'status': False, 'msg': "id不存在", 'error_code': 3})


def delete_info_api(request, user_id):
    type = request.DELETE.get('type')
    if type == 'praise':
        praise_id = request.DELETE.getlist('praise_id')
        for a_id in praise_id:
            UserPraise.objects.filter(id=a_id).update(display_status=False)
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


def praise_info_api(request, user_id):
    praise_info = []
    praise_number = 0
    post_ids = list(Post.objects.filter(writer_id=user_id).values_list('id', flat=True))
    for post_id in post_ids:
        user_praises = UserPraise.objects.filter(post_id=post_ids).select_related('post', 'user')
        if user_praises:
            post_photo = PostPhotos.objects.filter(post_id=post_id)[0].pic.url
            for praise in user_praises:
                praise_number += 1
                praise_info.append({
                    'info_id': praise.id,
                    'read_status': praise.read_status,
                    'person_id': praise.user_id,
                    'person_avatar': praise.user.avatar.url,
                    'person_name': praise.user.username,
                    'post_id': post_id,
                    'post_photo': post_photo,
                })
            user_praises.update(read_status=True)
        else:
            continue
    return JsonResponse({
        'user_id': user_id,
        'praise_info_number': praise_number,
        'praise_info': praise_info,
    })


def post_api(request):
    if request.method == 'DELETE':
        user_id = request.DELETE.get('user_id')
        post_id = request.DELETE.get('post_id')
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist as e:
            print(e)
            return JsonResponse({'status': False, 'msg': "帖子不存在"})
        else:
            if post.id != int(user_id):
                return JsonResponse({'status': False, 'msg': "无权限"})
            else:
                post.display_status = False
                post.save()
                return JsonResponse({'status': True})


def watching_bar_api(request, user_id):
    if request.method == 'DELETE':
        bar_id = request.DELETE.get('bar_id')
        UserWatching.objects.filter(bar_id=bar_id, user_id=int(user_id)).update(display_status=False)
        return JsonResponse({'status': True})
    if request.method == 'GET':
        bar_msg = []
        user_watching = UserWatching.objects.select_related('bar').filter(user_id=user_id)
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


def msg_api(request, user_id):
    if request.method == 'DELETE':
        type = request.DELETE.get('type')
        if type == 'watching':
            watching_ids = request.DELETE.getlist('watching_ids')
            for i in watching_ids:
                UserWatching.objects.filter(id=i).update(display_status=False)
        elif type == 'following':
            following_ids = request.DELETE.getlist('following_ids')
            for i in following_ids:
                UserFollow.objects.filter(id=i).update(display_status=False)
        else:
            return JsonResponse({'status': False, 'msg': '类型错误', 'error_code': 2})
        return JsonResponse({'status': True})
    if request.method == 'GET':
        new_follower = []
        new_watcher = []
        followers = UserFollow.objects.select_related('user').filter(follower_id=int(user_id), display_status=True)[10]
        new_follower_number = followers.count()
        for follower in followers:
            person  = follower.user.user
            new_follower.append({
                'id': follower.id,
                'user': person.id,
                'avatar': person.user.avatar.url,
                'username': person.username,
                'read_status': follower.read_status,
            })
        followers.objects.update(read_status=True)
        bar_ids = PostBars.objects.filter(master_id=user_id).values_list('id', flat=True)
        watchers = UserWatching.objects.filter(bar_id__in=bar_ids).select_related('user', 'user__user')[10]
        new_watcher_number = watchers.count()
        for watcher in watchers:
            person = watcher.user
            new_watcher.append({
                'id': watcher.id,
                'user': person.user_id,
                'avatar': person.user.avatar.url,
                'username': person.user.username,
                'read_status': watcher.read_status,
            })
        return JsonResponse({
            'user_id': int(user_id),
            'limit': 10,
            'number': new_follower_number + new_watcher_number,
            'new_follower_number': new_follower_number,
            'new_follower': new_follower,
            'new_watcher_number': new_watcher_number,
            'new_watcher': new_watcher,
        })


def user_concern_api(request, user_id):

    if int(request.session.get('id', 0)) != int(user_id):
        return JsonResponse({'status': False, 'error_code': 1, 'msg': "无权限"})

    if request.method == 'DELETE':
        delete_id = request.DELETE.get('user_id')
        temp = UserFollow.objects.filter(user__user_id=user_id, follower_id=delete_id)
        if temp:
            temp.update(display_status=False, mutual_following=False)
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
            UserFollow.objects.update_or_create(Q(follower_id=concern_id) & Q(user__user_id=user_id),
                                                defaults={'mutual_following': flag, 'display_status': True})
            return JsonResponse({'status': True})


def user_follower_api(request, user_id):
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

def user_collection_api(request, user_id):
    try:
        user = UserDetailMsg.objects.get(user_id=user_id)
    except Exception as e:
        print(e)
        return JsonResponse({'status': False, 'msg': "不存在"})
    if request.method == 'DELETE':
        post_id = request.DELETE.get('post_id')
        user.collections.filter(post_id=post_id).delete()
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
            })
        return JsonResponse({
            'user_id': user_id,
            'collection_number': collection_number,
            'collections': collections
        })

def personal_center_api(request, user_id):
    try:
        user = UserAll.objects.get(id=user_id)
    except UserAll.DoesNotExist as e:
        print(e)
        return JsonResponse({'status': False, 'msg': "用户不存在"})
    else:
        if request.method == 'GET':
            return JsonResponse({
                'user_id': user_id,
                'username': user.username,
                'gender': user.user_msg.gender,
                'description': user.user_msg.description,
                'birthday': str(user.user_msg.birthday),
                'avatar': user.avatar.url,
                'follower_number': user.user_msg.follow.count(),
                'collection_number': user.user_msg.collections.count(),
                'concern_number': user.user_msg.follow.count(),
                'watched_bar_number': user.user_msg.watching.count(),
                'background_pic': user.user_msg.background_pic.url,
            })
        # 修改个人信息
        if request.method == 'POST':
            username = request.POST.get('username', None)
            description = request.POST.get('description', None)
            gender = request.POST.get('gender', 0)
            birthday = request.POST.get('birthday', None)
            interests = request.POST.getlist('interests', None)
            if UserAll.objects.filter(Q(id!=user_id) & Q(username=username)):
                return JsonResponse({'status': False, 'msg': "用户名已经存在"})
            else:
                user.username = username
            if description:
                user.user_msg.description = description
            if gender:
                user.user_msg.gender = gender
            if re.match(r'(\w+){3,4}-(\w+){2}-(\w+){2}', birthday):
                print(birthday)
                user.user_msg.birthday = birthday
            if interests:
                for i in interests:
                    try:
                        user.user_msg.interest.add(Tags.objects.get(type=i))
                    except Exception as e:
                        print(e)
                        continue
            user.save()
            return JsonResponse({'status': True})

def pwd_reset(request, user_id):
    old_pwd = request.POST.get('old_pwd')
    new_pwd = request.POST.get('new_pwd')
    a_user = UserClass(id=user_id)
    if a_user.revise_pwd(old_pwd, new_pwd):
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status': False, 'msg': "原密码错误"})


def upload_photo(request):
    user_id = request.POST.get('user_id')
    if int(request.session.get('id')) != int(user_id):
        return JsonResponse({'status': False, 'msg': "无权限"})
    type = request.POST.get('type')
    user = UserClassForProject(id=user_id)
    if not user.check_user():
        return JsonResponse({'status': False, 'msg': "用户不存在"})
    else:
        if type == 'avatar':
            if user.upload_avatar(request):
                return JsonResponse({'status': True})
            else:
                return JsonResponse({'status': False, 'msg': "图片格式错误或太大了"})
        elif type == 'background':
            if user.upload_background(request):
                return JsonResponse({'status': True})
            else:
                return JsonResponse({'status': False, 'msg': "图片格式错误或太大了"})
        else:
            return JsonResponse({'status': False, 'msg': "指定类型不存在"})
