from django.shortcuts import render, HttpResponse
from MyTieba import settings
from django.db.models import Max, Avg, F, Q, Min, Count, Sum
from django.core.mail import send_mail
from app_api.models import *
import json
import re
import hashlib
import random

class JsonResponse(HttpResponse):
    def __init__(self, content,
                 status=None,
                 content_type='application/json',
                 charset='UTF-8'):
        super(JsonResponse, self).__init__(json.dumps(content),
                                           status=status,
                                           content_type=content_type,
                                           charset=charset)


def login_required(func):
    def wrapper(request,*args, **kwargs):
        if request.session.get('id'):
            decorate_func = func(request, *args, **kwargs)
            return decorate_func
        else:
            return JsonResponse({'status': False, 'msg': "未登录"})
    return wrapper


def login_api(request):
    name = request.POST.get('username')
    password = request.POST.get('password')
    user = UserAll.objects.filter(username=name)
    if user:
        user = user[0]
        if hashlib.sha1(password.encode('utf-8')).hexdigest() == user.password:
            return JsonResponse({'status': True, 'msg': "登录成功"})
        else:
            return JsonResponse({'status': False, 'msg': "密码错误"})
    else:
        return JsonResponse({'status': False, 'msg': "用户不存在"})


def check_email(email):
    email_flag = re.compile('^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
    if re.match(email_flag, email):
        return True
    else:
        return False


def email_api(request):
    time = 1
    email = request.GET.get('email')
    if check_email(email):
        title = "验证码"
        code = ""
        while(time <= 6):
            code += str(random.randint(0, 9))
            time += 1
        body = "你的验证码是:{}".format(code)
        request.session['code'] = code
        send_mail(subject=title, message=body, recipient_list=[email], from_email=settings.EMAIL_HOST_USER)
        return JsonResponse({'status': True, 'msg': "发送邮件成功"})


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