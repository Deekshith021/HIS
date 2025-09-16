from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from his.views import LoginPageView, DashboardView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root URL goes to login
    path('', LoginPageView.as_view(), name='login'),
    
    # Dashboard URL
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Logout
    path('logout/', LogoutView.as_view(), name='logout'),

    # JWT auth
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # All REST API routes
    path('api/', include('his.urls')),
]
