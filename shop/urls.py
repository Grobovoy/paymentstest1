from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("anketa/<int:pk>/", views.anketa_detail, name="anketa"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("topup/", views.topup, name="topup"),
    path("topup/start/", views.topup_start, name="topup_start"),
    path("topup/return/", views.topup_return, name="topup_return"),
    path("orders/", views.orders, name="orders"),
    path("rules/", views.rules, name="rules"),
    path("api/webhook/lava/", views.lava_webhook, name="lava_webhook"),
]
