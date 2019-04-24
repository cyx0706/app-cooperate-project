from django.conf.urls import url
from app_api import views
urlpatterns = [
    url(r'test/delete', views.test_delete),
]

