"""
Custom exception handler for the API
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    response = exception_handler(exc, context)

    # Handle standard Python exceptions that aren't DRF exceptions
    if response is None:
        if isinstance(exc, PermissionError):
            return Response({
                'success': False,
                'error': {
                    'code': 403,
                    'message': str(exc),
                    'detail': 'You do not have permission to perform this action.'
                }
            }, status=status.HTTP_403_FORBIDDEN)

    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': str(exc),
                'detail': response.data,
            }
        }
        # Avoid double nesting if using custom responses elsewhere
        if 'success' in response.data:
            custom_response_data = response.data
            
        response.data = custom_response_data

    return response
