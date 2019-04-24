from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render, HttpResponse

def test(request):
    return render(request, 'test.html')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^mytieba.api/', include('app_api.urls')),
    url(r'^test/', test)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

