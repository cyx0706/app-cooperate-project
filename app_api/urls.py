from django.conf.urls import url,include
from app_api import views

urlpatterns = [
    url(r'test/delete', views.test_delete),
    url(r'test/list', views.test_list),
    url(r'email$', views.email_api),
    url(r'logout', views.logout_api),
    url(r'email/vertify', views.check_email_code_api),
    url(r'register', views.register_api),
    url(r'login', views.login_api),
    url(r'user/(?P<user_id>\w+)/', include([
        url(r'floor_comment-info', views.floor_comment_info_api),
        url(r'comment-info', views.comment_info_api),


    ]))
]

