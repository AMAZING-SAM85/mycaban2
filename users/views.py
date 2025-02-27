from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import *
from .serializers import (
    UserRegistrationSerializer,
    OTPVerificationSerializer,
    OTPResendSerializer,
    UserLoginSerializer,
    UserProfileSerializer
)
from .utils import generate_otp, send_otp_email
from rest_framework.decorators import action


User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Creates a new user account with the provided details and sends an OTP for verification.
    The user must verify their email using the OTP before the account becomes active.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register new user",
        description="Create a new user account and send verification OTP",
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "email": {"type": "string"}
                }
            }
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = generate_otp()
        print(otp)
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        send_otp_email(user, otp)

        return Response({
            'message': 'Registration successful. Please check your email for verification.',
            'email': user.email
        }, status=status.HTTP_201_CREATED)

class OTPVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Verify user account with OTP",
        description="Verify user's email using the OTP sent during registration",
        request=OTPVerificationSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "refresh": {"type": "string"},
                    "access": {"type": "string"},
                    "user": {"type": "object"}  # Add user information to the response
                }
            }
        }
    )
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
 
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not user.otp or user.otp != otp or not user.is_otp_valid():
            return Response(
                {'error': 'Invalid or expired OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.is_verified = True
        user.otp = None
        user.otp_created_at = None
        user.save()

        refresh = RefreshToken.for_user(user)
        user_data = UserProfileSerializer(user).data  # Serialize user information

        return Response({
            'message': 'Account verified successfully',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data  # Include user information in the response
        })

class OTPResendView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Resend verification OTP",
        description="Generate and send a new OTP to the user's email",
        request=OTPResendSerializer,
        responses={
            200: {"description": "OTP sent successfully"},
            404: {"description": "User not found or already verified"}
        }
    )
    def post(self, request):
        serializer = OTPResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found or already activated'},
                status=status.HTTP_404_NOT_FOUND
            )

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        send_otp_email(user, otp)

        return Response({
            'message': 'New OTP sent to your email'
        })

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="User login",
        description="Authenticate user and return tokens",
        request=UserLoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string"},
                    "access": {"type": "string"},
                    "user": {"type": "object"}
                }
            }
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is not verified. Please verify your email.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        user_data = UserProfileSerializer(user).data

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        })



class UserSettingsViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSettingsSerializer

    @extend_schema(
        description="Get or update user preferences",
        responses={200: UserSettingsSerializer}
    )
    @action(detail=False, methods=['get', 'put'])
    def preferences(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        description="Change user password",
        request=ChangePasswordSerializer,
        responses={200: {"message": "Password updated successfully"}}
    )
    @action(detail=False, methods=['post'], serializer_class=ChangePasswordSerializer)
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({'error': 'Current password is incorrect'}, status=400)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'Password updated successfully'})

    @action(detail=False, methods=['post'], serializer_class=PhoneVerificationSerializer)
    def verify_phone(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Implement your phone verification logic here
        # Send verification code via SMS
        return Response({'status': 'Verification code sent'})

    @action(detail=False, methods=['post'], serializer_class=GovernmentIDSerializer)
    def upload_id(self, request):
        # Implement document upload logic
        # Save document to secure storage
        return Response({'status': 'ID document uploaded successfully'})

    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        user = request.user
        # Add any additional cleanup logic
        user.delete()
        return Response({'status': 'Account deleted successfully'})