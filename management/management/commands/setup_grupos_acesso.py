from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = "Cria/atualiza grupos padrão de acesso com permissões controladas."

    def handle(self, *args, **options):
        app_label = "management"

        # Grupo ADM: acesso total a tudo que pertence ao app management.
        adm_group, _ = Group.objects.get_or_create(name="ADM")
        adm_permissions = Permission.objects.filter(
            content_type__app_label=app_label)
        adm_group.permissions.set(adm_permissions)

        # Grupo com acesso apenas de leitura para eventos, banhos e tarefas.
        leitura_group, _ = Group.objects.get_or_create(
            name="LEITURA_EVENTOS_BANHOS_TAREFAS")
        leitura_permissions = Permission.objects.filter(
            content_type__app_label=app_label,
            codename__in=[
                "view_evento",
                "view_banho",
                "view_tarefa",
            ],
        )
        leitura_group.permissions.set(leitura_permissions)

        # Grupo de toque (mapeado para acesso de leitura de colaboradores + eventos, banhos e tarefas).
        toque_group, _ = Group.objects.get_or_create(
            name="TOQUE_EVENTOS_BANHOS_TAREFAS")
        toque_permissions = Permission.objects.filter(
            content_type__app_label=app_label,
            codename__in=[
                "view_medium",
                "view_evento",
                "view_banho",
                "view_tarefa",
            ],
        )
        toque_group.permissions.set(toque_permissions)

        self.stdout.write(self.style.SUCCESS(
            "Grupos configurados com sucesso."))
        self.stdout.write("- ADM: acesso total no app management")
        self.stdout.write(
            "- LEITURA_EVENTOS_BANHOS_TAREFAS: somente visualização")
        self.stdout.write(
            "- TOQUE_EVENTOS_BANHOS_TAREFAS: leitura de toque(colaboradores), eventos, banhos e tarefas")
