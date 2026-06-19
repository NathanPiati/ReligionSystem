from .models import Material, MovimentacaoEstoque
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
    list_display = ('titulo', 'tipo', 'data', 'horario')
    list_filter = ('tipo', 'data')


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
