from .models import ActivityLog, Material, MovimentacaoEstoque, ListaCompra, ListaCompraItem
from django.contrib import admin
from .models import Medium, Evento, Presenca, Financeiro


@admin.register(Medium)
class MediumAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'nome_religioso',
                    'papel', 'cargo', 'telefone', 'ativo')
    search_fields = ('nome_completo', 'nome_religioso', 'cargo')
    list_filter = ('ativo', 'papel')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data', 'horario',
                    'gira_concluida', 'hora_inicio', 'hora_fim')
    list_filter = ('tipo', 'data', 'gira_concluida')


@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'valor', 'data')
    list_filter = ('tipo', 'data')


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ('medium', 'evento', 'presente')
    list_filter = ('evento', 'presente')


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'quantidade_atual', 'unidade_medida')
    search_fields = ('nome',)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('material', 'quantidade', 'tipo', 'data')
    list_filter = ('tipo', 'data')


class ListaCompraItemInline(admin.TabularInline):
    model = ListaCompraItem
    extra = 0
    readonly_fields = (
        'material',
        'material_nome',
        'categoria',
        'quantidade_atual',
        'quantidade_minima',
        'unidade_medida',
        'valor_previsto',
    )
    can_delete = False


@admin.register(ListaCompra)
class ListaCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'responsavel', 'status',
                    'total_previsto', 'data_criacao')
    list_filter = ('status', 'data_criacao')
    search_fields = ('id', 'responsavel__nome_completo')
    inlines = [ListaCompraItemInline]


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'username_snapshot',
                    'action_label', 'method', 'path', 'status_code', 'ip_address')
    list_filter = ('method', 'status_code', 'created_at')
    search_fields = ('username_snapshot', 'action_label',
                     'path', 'ip_address', 'user_agent')
    readonly_fields = (
        'created_at',
        'user',
        'username_snapshot',
        'action_label',
        'method',
        'path',
        'status_code',
        'ip_address',
        'user_agent',
    )

    def has_add_permission(self, request):
        return False

    def _is_adm_group(self, request):
        return request.user.is_authenticated and request.user.groups.filter(name='ADM').exists()

    def has_module_permission(self, request):
        return self._is_adm_group(request)

    def has_view_permission(self, request, obj=None):
        return self._is_adm_group(request)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
