from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('common/', include('common.urls')),
    path('whirligig/', include('whirligig.urls')),
    path('jeopardy/', include('jeopardy.urls')),
    path('weakest/', include('weakest.urls')),
    path('feud/', include('feud.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
