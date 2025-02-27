from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from urllib.parse import parse_qs

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
