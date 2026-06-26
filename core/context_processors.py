from django.conf import settings


def app_version(request):
    return {
        'versao': settings.APP_VERSION,
    }
