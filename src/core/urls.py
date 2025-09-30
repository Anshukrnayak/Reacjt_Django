from django.urls import path
from . import views


urlpatterns=[
    path('designations/',views.DesignationApiView.as_view(),name='designation'),
    path('designations/<int:pk>/',views.DesignationAPIViewRetrieve.as_view(),name='designation_retrieve')
]