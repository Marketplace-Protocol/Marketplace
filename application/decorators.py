import functools
import json

from flask import session, abort

from loguru import logger

from application.controllers.user_session_controller import UserSessionController
from application.errors import UserAuthenticationFailure, ValidationError, DataAlreadyExists, \
    UserAuthenticationRequired, ContextValidationError, DataNotFound
from application.utils import _convert_from_camel_to_snake


def authenticated_required(func):
    """Decorator to check if the user is authenticated."""
    def wrapper(*args, **kwargs):
        if 'user_id' in session:
            try:
                user = UserSessionController().load_user(user_id=session['user_id'])
                if user:
                    return func(*args, **kwargs)
                else:
                    raise UserAuthenticationRequired("User is not authenticated")
            except Exception as e:
                raise UserAuthenticationRequired(f"Authentication Failure: {str(e)}")
        else:
            raise UserAuthenticationRequired(f"Authentication Failure: Missing user ID")

    wrapper.__name__ = func.__name__
    wrapper.original_function = func
    return wrapper


def user_session_management_error_handler(func):
    """Decorator to handle errors in a function.
    Args:
    func: The function to decorate.

    Returns:
    The decorated function.
    """
    @functools.wraps(func)  # Preserve original function metadata
    def wrapper(*args, **kwargs):
        err = None
        status_code = 200
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            err = e
            status_code = 400
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Request parameter is malformed...'
                    }
                }
            ), status_code
        except UserAuthenticationFailure as e:
            err = e
            status_code = 401
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Authentication failed. Please make sure your input is correct!'
                    }
                }
            ), status_code
        except UserAuthenticationRequired as e:
            err = e
            status_code = 403
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Authentication required. Please log in to access this feature'
                    }
                }
            ), status_code
        except DataAlreadyExists as e:
            err = e
            status_code = 409
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Whoops. Specified username already exists. '
                                         'Please try again with different username.'
                    }
                }
            ), status_code

        except Exception as e:
            err = e
            status_code = 500
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Unknown failure.'
                    }
                }
            ), status_code
        finally:
            function_name = func.__name__
            if err:
                logger.info("Marketplace returning error response", kv={
                    'status_code': status_code,
                    'error_type': _convert_from_camel_to_snake(err.__class__.__name__),
                    'error_details': str(err),
                    'function_name': function_name
                })

    return wrapper


def offer_generation_error_handler(func):
    """Decorator to handle errors in a function.
    Args:
    func: The function to decorate.

    Returns:
    The decorated function.
    """
    @functools.wraps(func)  # Preserve original function metadata
    def wrapper(*args, **kwargs):
        err = None
        status_code = 200
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            err = e
            status_code = 400
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Request parameter is malformed...'
                    }
                }
            ), status_code
        except ContextValidationError as e:
            err = e
            status_code = 422
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Unprocessable user request. Please try again!'
                    }
                }
            ), status_code
        except Exception as e:
            err = e
            status_code = 500
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Unknown failure.'
                    }
                }
            ), status_code
        finally:
            function_name = func.__name__
            if err:
                logger.info("Marketplace returning error response", kv={
                    'status_code': status_code,
                    'error_type': _convert_from_camel_to_snake(err.__class__.__name__),
                    'error_details': str(err),
                    'function_name': function_name
                })

    return wrapper


def stripe_webhook_error_handler(func):
    @functools.wraps(func)  # Preserve original function metadata
    def wrapper(*args, **kwargs):
        err = None
        status_code = 200
        try:
            return func(*args, **kwargs)
        except DataNotFound as e:
            err = e
            status_code = 404
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Data not found'
                    }
                }
            ), status_code
        except ValidationError as e:
            err = e
            status_code = 400
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Data not found'
                    }
                }
            ), status_code
        except (ContextValidationError, NotImplemented, KeyError) as e:
            err = e
            status_code = 422
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Data not found'
                    }
                }
            ), status_code
        except Exception as e:
            err = e
            status_code = 500
            return json.dumps(
                {
                    'error_details': {
                        'error_type': _convert_from_camel_to_snake(e.__class__.__name__),
                        'error_details': str(e),
                        'error_message': 'Unknown failure.'
                    }
                }
            ), status_code
        finally:
            function_name = func.__name__
            if err:
                logger.info("Marketplace returning error response", kv={
                    'status_code': status_code,
                    'error_type': _convert_from_camel_to_snake(err.__class__.__name__),
                    'error_details': str(err),
                    'function_name': function_name
                })

    return wrapper