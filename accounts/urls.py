from django.conf.urls import url, include
from django.views.generic import TemplateView

from .accounts_api import RegisterAPI, LoginAPI, UserAPI  # ProfileAPI

from .analyzer_api import *
from knox import views as knox_views

urlpatterns = [
    url("api/auth", include("knox.urls")),
    url("api/auth/register", RegisterAPI.as_view()),
    url("api/auth/login", LoginAPI.as_view()),
    url("api/auth/user", UserAPI.as_view()),
    url("api/auth/logout", knox_views.LogoutView.as_view(), name="knox_logout"),
    url("api/create/profile", create_customer_profile, name="profile"),
    url("api/get/categories", get_priority_categories, name="categories"),
    url("api/post/savings", get_saving_plan, name="priority"),
    url("api/get/analytics", get_trend_data, name="analytics"),
    url("api/get/customer", get_customer_info, name="customer_info"),
]
