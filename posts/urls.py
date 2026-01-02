from django.urls import path
from . import views


urlpatterns = [
	path('', views.feed, name='feed'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('add/', views.add_post, name='add_post'),
	path('edit/<int:pk>/', views.edit_post, name='edit_post'),
	path('delete/<int:pk>/', views.delete_post, name='delete_post'),
	path('like/<int:pk>/', views.toggle_like, name='toggle_like'),
	path('favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
	path('categories/add/', views.add_category, name='add_category'),
]