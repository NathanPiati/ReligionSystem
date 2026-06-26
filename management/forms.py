from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from .models import Medium, Evento, Financeiro, Material, MovimentacaoEstoque, Tarefa, Banho


User = get_user_model()


class MediumForm(forms.ModelForm):
    CARGO_CHOICES = [
        ('', 'Selecione um cargo'),
        ('Médium', 'Médium'),
        ('Cambone de Esquerda', 'Cambone de Esquerda'),
        ('Cambone de Direita', 'Cambone de Direita'),
        ('Cambone Geral', 'Cambone Geral'),
        ('Diretor', 'Diretor'),
        ('Atabaqueiro', 'Atabaqueiro'),
        ('Curimbeiro', 'Curimbeiro'),
        ('Dirigente', 'Dirigente'),
        ('Coordenador', 'Coordenador'),
        ('Atendimento', 'Atendimento'),
        ('Recepção', 'Recepção'),
        ('Apoio', 'Apoio'),
        ('Outro', 'Outro'),
    ]

    class Meta:
        model = Medium
        fields = ['nome_completo', 'nome_religioso',
                  'data_nascimento', 'telefone', 'email', 'ativo', 'papel', 'cargo']
        labels = {
            'nome_completo': 'Nome completo',
            'nome_religioso': 'Nome religioso',
            'data_nascimento': 'Data de nascimento',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'ativo': 'Ativo',
            'papel': 'Função',
            'cargo': 'Cargo',
        }
        help_texts = {
            'papel': 'Função do colaborador dentro do centro',
            'cargo': 'Cargo ou função específica dentro da função',
        }
        widgets = {
            'cargo': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cargo_choices = list(self.CARGO_CHOICES)
        cargo_atual = self.initial.get('cargo')
        if cargo_atual and all(valor != cargo_atual for valor, _ in cargo_choices):
            cargo_choices.append((cargo_atual, cargo_atual))
        self.fields['cargo'].widget = forms.Select(choices=cargo_choices)


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'titulo',
            'tipo',
            'data',
            'horario',
            'hora_inicio',
            'hora_fim',
            'descricao',
            'recados_entidades',
            'gira_concluida',
        ]
        labels = {
            'titulo': 'Título',
            'tipo': 'Tipo',
            'data': 'Data',
            'horario': 'Horário previsto',
            'hora_inicio': 'Hora de início da gira',
            'hora_fim': 'Hora de término da gira',
            'descricao': 'Descrição do evento',
            'recados_entidades': 'Recados das entidades',
            'gira_concluida': 'Gira concluída',
        }
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'horario': forms.TimeInput(attrs={'type': 'time'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'recados_entidades': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fim = cleaned_data.get('hora_fim')

        if hora_inicio and hora_fim and hora_fim < hora_inicio:
            self.add_error(
                'hora_fim', 'A hora de término não pode ser menor que a hora de início.')

        return cleaned_data


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


class GroupPermissionForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related('content_type').order_by(
            'content_type__app_label', 'content_type__model', 'name'),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-select', 'size': 14}),
        label='Permissões',
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Coordenação'}),
        }


class UserGroupAssignmentForm(forms.Form):
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by('name'),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-select', 'size': 10}),
        label='Grupos',
    )


class UserSelectorForm(forms.Form):
    usuario = forms.ModelChoiceField(
        queryset=User.objects.order_by('username'),
        required=False,
        empty_label='Selecione um usuário',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Usuário',
    )


class GroupSelectorForm(forms.Form):
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.order_by('name'),
        required=False,
        empty_label='Novo grupo',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Grupo',
    )


class UserCreationWithGroupsForm(UserCreationForm):
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by('name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        label='Grupos iniciais',
    )
    is_staff = forms.BooleanField(
        required=False,
        initial=True,
        label='Pode acessar o admin Django',
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Usuário ativo',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'is_staff', 'is_active', 'grupos')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Usuário para login'})
        self.fields['email'].required = False
        self.fields['email'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Email (opcional)'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.is_staff = self.cleaned_data.get('is_staff', False)
        user.is_active = self.cleaned_data.get('is_active', True)

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get('grupos'))

        return user
