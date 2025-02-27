from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from urllib.parse import parse_qs
import logging

# Set up logging
logger = logging.getLogger('django')
class WebSocketAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract token from the query string.
        token = self.get_token_from_scope(scope)
        if token:
            try:
                jwt_authenticator = JWTAuthentication()
                # Validate the token (synchronously) 
                validated_token = jwt_authenticator.get_validated_token(token)
                # Retrieve the user associated with the validated token in an async-safe manner
                user = await database_sync_to_async(jwt_authenticator.get_user)(validated_token)
                scope['user'] = user if user is not None else AnonymousUser()
            except Exception as e:
                # Optionally, log the exception for debugging:
                # print("JWT validation error:", e)
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
    
    def get_token_from_scope(self, scope):
        """
        Extracts the 'token' parameter from the query string.
        For example, if the client connects with:
            ws://127.0.0.1:8000/ws/requests/?token=YOUR_JWT_TOKEN
        this method returns YOUR_JWT_TOKEN.
        """
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token_list = query_params.get('token')
        if token_list:
            return token_list[0]
        return None


class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for token-based authentication in WebSockets
    """
    
    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Log query parameters for debugging
        logger.debug(f"WebSocket query params: {query_params}")
        
        token = None
        if 'token' in query_params:
            token = query_params['token'][0]
            # Remove any trailing slashes from token
            if token.endswith('/'):
                token = token[:-1]
        
        # Set the user in the scope
        if token:
            # Authenticate using JWT token
            user = await self.get_user_from_token(token)
            if user:
                scope['user'] = user
                logger.debug(f"Authenticated user: {user.id}")
            else:
                scope['user'] = AnonymousUser()
                logger.debug("Failed to authenticate user with provided token")
        else:
            scope['user'] = AnonymousUser()
            logger.debug("No token provided, setting AnonymousUser")
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Get the user associated with the given token
        """
        try:
            # Initialize JWT authentication
            jwt_auth = JWTAuthentication()
            
            # Validate token
            validated_token = jwt_auth.get_validated_token(token)
            
            # Get user from validated token
            user = jwt_auth.get_user(validated_token)
            return user
        except Exception as e:
            # Log any errors for debugging
            logger.error(f"Token authentication error: {str(e)}")
            return None