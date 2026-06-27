import logging

from management.models import ActivityLog

logger = logging.getLogger('umbanda')

MUTATION_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
SENSITIVE_KEYS = {
    'csrfmiddlewaretoken',
    'password',
    'password1',
    'password2',
    'new_password1',
    'new_password2',
}
DETAIL_KEYS = (
    'nome',
    'nome_completo',
    'titulo',
    'descricao',
    'tipo',
    'categoria',
    'valor',
    'status',
    'material',
    'medium',
    'colaborador_responsavel',
)


def _trim(value, limit):
    text = (value or '').strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1] + '...'


def _get_operation_name(request, route_name):
    name = (route_name or '').lower()
    if request.method == 'DELETE' or 'delete' in name or 'excluir' in name:
        return 'Exclusão'
    if request.method == 'POST' and ('criar' in name or 'create' in name):
        return 'Criação'
    if request.method in {'PUT', 'PATCH'} or 'editar' in name or 'update' in name:
        return 'Edição'
    if request.method == 'POST':
        return 'Ação'
    return request.method


def _extract_payload_details(request):
    if request.method not in MUTATION_METHODS:
        return ''

    parts = []
    for key in DETAIL_KEYS:
        value = request.POST.get(key)
        if value:
            parts.append(f'{key}={_trim(value, 24)}')

    itens_compra = [k for k in request.POST.keys() if k.startswith(
        'valor_item_') and request.POST.get(k)]
    if itens_compra:
        parts.append(f'itens_compra={len(itens_compra)}')

    # Se não encontrou chaves de interesse, adiciona até 2 chaves genéricas não sensíveis.
    if not parts:
        generic = []
        for key, value in request.POST.items():
            if key in SENSITIVE_KEYS:
                continue
            if not value:
                continue
            generic.append(f'{key}={_trim(value, 18)}')
            if len(generic) == 2:
                break
        parts.extend(generic)

    return '; '.join(parts)


def _build_action_label(request, status_code):
    resolver_match = getattr(request, 'resolver_match', None)
    route_name = ''
    if resolver_match and resolver_match.url_name:
        route_name = resolver_match.url_name

    path_label = request.path.strip('/') or 'raiz'
    status_hint = 'sucesso' if 200 <= int(status_code or 0) < 400 else 'falha'
    operation = _get_operation_name(request, route_name)
    base = route_name.replace('_', ' ').strip(
    ).title() if route_name else path_label

    target = ''
    if resolver_match and resolver_match.kwargs:
        identifiers = []
        for key in ('pk', 'id'):
            if key in resolver_match.kwargs:
                identifiers.append(f'{key}={resolver_match.kwargs[key]}')
        if identifiers:
            target = f' [{", ".join(identifiers)}]'

    details = _extract_payload_details(request)
    detail_suffix = f' | {details}' if details else ''
    text = f'{operation} em {base}{target} ({status_hint}){detail_suffix}'
    return _trim(text, 200)


def _extract_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


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

        # Persiste somente ações de alteração para focar no histórico de mudanças.
        if request.method not in MUTATION_METHODS:
            return response

        # Ignora rotas estáticas para reduzir ruído no histórico de atividades.
        if request.path.startswith('/static/'):
            return response

        try:
            user_obj = request.user if hasattr(
                request, 'user') and request.user.is_authenticated else None
            ActivityLog.objects.create(
                user=user_obj,
                username_snapshot=user if user not in {
                    'unknown', 'Anonymous'} else '',
                method=request.method,
                path=request.path[:255],
                action_label=_build_action_label(
                    request, getattr(response, 'status_code', 0) or 0),
                status_code=getattr(response, 'status_code', 0) or 0,
                ip_address=_extract_client_ip(request),
                user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:255],
            )
        except Exception:
            logger.exception(
                'Falha ao persistir ActivityLog para %s %s', request.method, request.path)

        return response
