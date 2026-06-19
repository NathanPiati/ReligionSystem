from django import forms
from .models import Medium, Evento, Financeiro, Material, MovimentacaoEstoque, Tarefa, Banho


class MediumForm(forms.ModelForm):
    class Meta:
        model = Medium
        fields = ['nome_completo', 'nome_religioso',
                  'data_nascimento', 'telefone', 'email', 'ativo', 'papel', 'cargo']


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'tipo', 'data', 'horario', 'descricao']


class FinanceiroForm(forms.ModelForm):
    class Meta:
        model = Financeiro
        fields = ['descricao', 'valor', 'tipo', 'medium']


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['nome', 'categoria', 'quantidade_atual',
                  'quantidade_minima', 'unidade_medida']


class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['material', 'quantidade', 'tipo', 'observacao']


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['medium', 'titulo', 'descricao', 'data_vencimento', 'status']
        labels = {
            'medium': 'Colaborador',
            'titulo': 'Título',
            'descricao': 'Descrição',
            'data_vencimento': 'Data de vencimento',
            'status': 'Status',
        }
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
        }


class BanhoForm(forms.ModelForm):
    class Meta:
        model = Banho
        fields = ['titulo', 'tipo', 'data', 'horario',
                  'medium', 'entidade', 'descricao']
        labels = {
            'titulo': 'Nome do Banho',
            'tipo': 'Tipo de Banho',
            'data': 'Data',
            'horario': 'Horário',
            'medium': 'Responsável',
            'entidade': 'Entidade',
            'descricao': 'Descrição',
        }
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'horario': forms.TimeInput(attrs={'type': 'time'}),
        }
