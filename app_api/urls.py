from django.conf.urls import url,include
from app_api import views

urlpatterns = [
    url(r'test/delete', views.test_delete),
    url(r'test/list', views.test_list),
    url(r'test/session', views.test_session),
    url(r'test/sensitive_filter', views.test_sensitive_word),
    url(r'email$', views.email_api),
    url(r'logout', views.logout_api),
    url(r'email/vertify', views.check_email_code_api),
    url(r'register', views.register_api),
    url(r'login', views.login_api),
    url(r'find-back', views.find_pwd_api),
    url(r'posts$', views.home_api, name='posts'),
    url(r'postbar$', views.post_bar_api),
    url(r'search$', views.search_api),
    url(r'praise$', views.praise_api),
    url(r'post/(?P<post_id>\d+)/detail', views.post_msg_api),
    url(r'post/(?P<post_id>\d+)/comment', views.floor_msg_api),
    url(r'upload/photo', views.upload_photo),
    url(r'user/(?P<user_id>\d+)/', include([
        url(r'floor_comment-info', views.floor_comment_info_api),
        url(r'comment-info', views.comment_info_api),
        url(r'comment$', views.delete_comment_api),
        url(r'information$', views.delete_info_api),
        url(r'praise-info$', views.praise_info_api),
        url(r'watching$', views.watching_bar_api),
        url(r'msg$', views.msg_api),
        url(r'follow$', views.user_concern_api),
        url(r'follower$', views.user_follower_api),
        url(r'collection$', views.user_collection_api),
        url(r'info$', views.personal_center_api),
        url(r'reset-pwd$', views.pwd_reset),

    ]))
]

