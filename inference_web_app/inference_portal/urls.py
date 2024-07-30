from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('explore_apps', views.explore_apps, name='explore_apps'),
    path('explore_plugins', views.explore_plugins, name='explore_plugins'),
    path('explore_binaries', views.explore_binaries, name='explore_binaries'),
    path('explore_rest_apis', views.explore_rest_apis, name='explore_rest_apis'),
    path('payments', views.payments, name='payments'),
    path('profile_settings', views.profile_settings, name='profile_settings'),
    
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),
    path('my_purchase_orders', views.my_purchase_orders, name='my_purchase_orders'),
    path('my_sell_orders', views.my_sell_orders, name='my_sell_orders'),

    path('get_tfuel_balance', views.get_tfuel_balance, name='get_tfuel_balance'),
    path('check_tfuel_transaction', views.check_tfuel_transaction, name='check_tfuel_transaction'),
    path('checkout_page', views.checkout_page, name='checkout_page'),

    path('model_inference_apps', views.InferenceAppListView.as_view(), name='model_inference_apps'),
    path('model_inference_app_create', views.InferenceAppCreateView.as_view(), name='model_inference_app_create'),
    path('model_inference_app_edit/<int:pk>/', views.InferenceAppEditView.as_view(), name='model_inference_app_edit'),

    path('login', views.loginUser, name ='login'),
    path('register', views.registerUser, name ='register'),
    path('logout', views.logoutUser, name ='logout'),
]