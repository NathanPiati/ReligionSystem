import logging

logger = logging.getLogger('umbanda')


class RequestLoggingMiddleware:
    """Middleware simples que registra método, caminho, status e usuário."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            user = request.user.get_username() if hasattr(
                request, 'user') and request.user.is_authenticated else 'Anonymous'
        except Exception:
            user = 'unknown'
        logger.info('%s %s %s %s', request.method, request.path,
                    getattr(response, 'status_code', '-'), user)
        return response
