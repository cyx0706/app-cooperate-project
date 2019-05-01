from django.shortcuts import render, HttpResponse
from MyTieba import settings
from django.db.models import Max, Avg, F, Q, Min, Count, Sum
from django.core.mail import send_mail
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

    def check_uniqueness_name(self):
        if UserAll.objects.filter(username=self.username):
            return False
        return True


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
        while(time <= 6):
            code += str(random.randint(0, 9))
            time += 1
        body = "你的验证码是:{}".format(code)

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