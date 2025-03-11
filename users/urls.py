from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserRegistrationView, 
    OTPVerificationView, 
    OTPResendView, 
    LoginView,
    UserSettingsViewSet,
)

from rest_framework.routers import DefaultRouter
from .users import UserViewSet
from .rating import RatingViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('ratings', RatingViewSet, basename='rating')
router.register('settings', UserSettingsViewSet, basename='user-settings')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('verify-otp/', OTPVerificationView.as_view(), name='otp-verification'),
    path('resend-otp/', OTPResendView.as_view(), name='otp-resend'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += router.urls