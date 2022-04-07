# coding:utf-8
"""
  Time : 2022/4/3 3:04
  Author : vincent
  FileName: urls
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2022/4/3 3:04
"""
from django.conf.urls import url

from management import views

urlpatterns = [
    url(r'^login/', views.login, name='login'),
    url(r'^changeVerifyCode/', views.change_verify_code, name='changeVerifyCode'),
    url(r'^index/', views.index, name='index'),
    url(r'^logout/', views.logout, name='logout'),
    url(r'^home/', views.home, name='home'),
    url(r'^userManage/(?P<type>\w+)/', views.user_manage, name='userManage'),
    url(r'^tableData/(?P<type>\w+)/', views.table_data, name='tableData'),
    url(r'^updatePass/', views.update_pass, name='updatePass'),
    url(r'^presUpload/(?P<type>\w+)/', views.pres_upload, name='presUpload'),
    url(r'^presQuery/(?P<type>\w+)/', views.pres_query, name='presQuery'),
    url(r'^company/', views.get_hos_properties, name='company'),
    url(r'^addressManage/(?P<type>\w+)/', views.address_manage, name='addressManage')
]