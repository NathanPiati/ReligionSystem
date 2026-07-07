from datetime import date
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from .models import ActivityLog, Medium, Evento, Financeiro, Presenca, Material, Tarefa, Banho, ListaCompra, ListaCompraItem
from django.db.models import Sum, Q, Count, F
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import (
    MediumForm,
    EventoForm,
    FinanceiroForm,
    MaterialForm,
    MovimentacaoEstoqueForm,
    TarefaForm,
    BanhoForm,
    GroupPermissionForm,
    UserGroupAssignmentForm,
    UserCreationWithGroupsForm,
    UserSelectorForm,
    GroupSelectorForm,
)
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


User = get_user_model()


def can_access_admin_panel(user):
    return user.is_superuser or user.groups.filter(name='ADM').exists()


def can_access_activity_logs(user):
    return user.is_authenticated and user.groups.filter(name='ADM').exists()


def build_finance_chart_data(limit=6):
    monthly_rows = list(
        Financeiro.objects.annotate(month=TruncMonth('data'))
        .values('month')
        .annotate(
            entradas=Sum('valor', filter=Q(tipo='ENTRADA')),
            saídas=Sum('valor', filter=Q(tipo='SAIDA')),
        )
        .order_by('-month')[:limit]
    )
    monthly_rows.reverse()

    labels = [row['month'].strftime('%b/%Y').capitalize()
              for row in monthly_rows if row['month']]
    entradas = [float(row['entradas'] or 0) for row in monthly_rows]
    saidas = [float(row['saídas'] or 0) for row in monthly_rows]
    saldo = [entrada - saida for entrada, saida in zip(entradas, saidas)]

    return {
        'labels': labels,
        'entradas': entradas,
        'saidas': saidas,
        'saldo': saldo,
    }


def parse_currency_input(value: str) -> Decimal:
    raw = (value or '').strip().replace('R$', '').replace(' ', '')
    if not raw:
        return Decimal('0')

    if ',' in raw and '.' in raw:
        raw = raw.replace('.', '').replace(',', '.')
    elif ',' in raw:
        raw = raw.replace(',', '.')

    parsed = Decimal(raw)
    if parsed < 0:
        raise InvalidOperation
    return parsed


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.✅')
    return redirect('login')


@login_required
def painel_administrativo(request):
    if not can_access_admin_panel(request.user):
        raise PermissionDenied

    users = User.objects.prefetch_related('groups').order_by('username')
    groups = Group.objects.prefetch_related('permissions').order_by('name')
    permissions = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'name'
    )

    selected_group_id = request.POST.get(
        'grupo_id') or request.GET.get('grupo')
    selected_user_id = request.POST.get(
        'usuario_id') or request.GET.get('usuario')

    selected_group = groups.filter(pk=selected_group_id).first(
    ) if selected_group_id else groups.first()
    selected_user = users.filter(pk=selected_user_id).first(
    ) if selected_user_id else users.first()

    group_form = GroupPermissionForm(
        instance=selected_group) if selected_group else GroupPermissionForm()
    user_form = UserGroupAssignmentForm(
        initial={'grupos': selected_user.groups.all()} if selected_user else None
    )
    create_user_form = UserCreationWithGroupsForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_group':
            group_form = GroupPermissionForm(
                request.POST, instance=selected_group)
            if group_form.is_valid():
                group_form.save()
                messages.success(request, 'Grupo salvo com sucesso.')
                return redirect('painel_administrativo')
        elif action == 'save_user':
            if not selected_user_id:
                messages.error(
                    request, 'Selecione um usuário antes de salvar os grupos.')
                return redirect('painel_administrativo')
            selected_user = get_object_or_404(User, pk=selected_user_id)
            user_form = UserGroupAssignmentForm(request.POST)
            if user_form.is_valid():
                selected_user.groups.set(user_form.cleaned_data['grupos'])
                messages.success(
                    request, 'Grupos do usuário atualizados com sucesso.')
                return redirect('painel_administrativo')
        elif action == 'create_user':
            create_user_form = UserCreationWithGroupsForm(request.POST)
            if create_user_form.is_valid():
                new_user = create_user_form.save()
                messages.success(
                    request,
                    f'Usuário "{new_user.username}" criado e vinculado aos grupos selecionados.',
                )
                return redirect(f'{request.path}?usuario={new_user.pk}')

    context = {
        'users': users,
        'groups': groups,
        'permissions': permissions,
        'selected_group': selected_group,
        'selected_user': selected_user,
        'group_form': group_form,
        'user_form': user_form,
        'create_user_form': create_user_form,
        'group_selector_form': GroupSelectorForm(initial={'grupo': selected_group}),
        'user_selector_form': UserSelectorForm(initial={'usuario': selected_user}),
        'total_users': users.count(),
        'total_groups': groups.count(),
        'total_permissions': permissions.count(),
    }
    return render(request, 'management/painel_administrativo.html', context)


@login_required
def activity_logs(request):
    if not can_access_activity_logs(request.user):
        raise PermissionDenied

    logs = ActivityLog.objects.select_related('user').all()
    method = request.GET.get('method', '').strip().upper()
    status = request.GET.get('status', '').strip()
    search = request.GET.get('q', '').strip()

    if method:
        logs = logs.filter(method=method)

    if status.isdigit():
        logs = logs.filter(status_code=int(status))

    if search:
        logs = logs.filter(
            Q(username_snapshot__icontains=search)
            | Q(path__icontains=search)
            | Q(action_label__icontains=search)
        )

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'total_logs': logs.count(),
        'filtros': {
            'method': method,
            'status': status,
            'q': search,
        },
    }
    return render(request, 'management/activity_logs.html', context)


@login_required
def dashboard(request):
    total_membros = None
    proximos_eventos = []
    saldo_final = None
    financeiro_chart = None
    eventos_tipo_chart = None
    can_view_medium = request.user.has_perm('management.view_medium')
    can_view_evento = request.user.has_perm('management.view_evento')
    can_view_financeiro = request.user.has_perm('management.view_financeiro')

    if can_view_medium:
        total_membros = Medium.objects.filter(ativo=True).count()

    if can_view_evento:
        proximos_eventos = Evento.objects.all().order_by('data')[:5]
        tipo_labels = dict(Evento.TIPO_CHOICES)
        eventos_por_tipo = (
            Evento.objects.filter(data__gte=date.today())
            .values('tipo')
            .annotate(total=Count('id'))
            .order_by('tipo')
        )
        eventos_tipo_chart = {
            'labels': [tipo_labels[item['tipo']] for item in eventos_por_tipo],
            'values': [item['total'] for item in eventos_por_tipo],
        }

    if can_view_financeiro:
        saldo = Financeiro.objects.filter(tipo='ENTRADA').aggregate(Sum('valor'))[
            'valor__sum'] or 0
        despesas = Financeiro.objects.filter(tipo='SAIDA').aggregate(Sum('valor'))[
            'valor__sum'] or 0
        saldo_final = saldo - despesas
        financeiro_chart = build_finance_chart_data()

    context = {
        'total_membros': total_membros,
        'proximos_eventos': proximos_eventos,
        'saldo_final': saldo_final,
        'financeiro_chart': financeiro_chart,
        'eventos_tipo_chart': eventos_tipo_chart,
        'can_view_medium': can_view_medium,
        'can_view_evento': can_view_evento,
        'can_view_financeiro': can_view_financeiro,
    }
    return render(request, 'management/dashboard.html', context)


@permission_required('management.view_medium', raise_exception=True)
def lista_membros(request):
    membros = Medium.objects.all()
    return render(request, 'management/membros.html', {'membros': membros})


@permission_required('management.view_evento', raise_exception=True)
def lista_eventos(request):
    eventos = Evento.objects.all().order_by('-data', '-horario')

    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    status = request.GET.get('status', '').strip()
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()

    if q:
        eventos = eventos.filter(
            Q(titulo__icontains=q) | Q(descricao__icontains=q))

    if tipo:
        eventos = eventos.filter(tipo=tipo)

    if status == 'concluida':
        eventos = eventos.filter(gira_concluida=True)
    elif status == 'pendente':
        eventos = eventos.filter(gira_concluida=False)

    if data_inicio:
        eventos = eventos.filter(data__gte=data_inicio)

    if data_fim:
        eventos = eventos.filter(data__lte=data_fim)

    context = {
        'eventos': eventos,
        'tipos_evento': Evento.TIPO_CHOICES,
        'filtros': {
            'q': q,
            'tipo': tipo,
            'status': status,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        },
    }
    return render(request, 'management/eventos.html', context)


@permission_required('management.view_financeiro', raise_exception=True)
def financeiro(request):
    transacoes = Financeiro.objects.all().order_by('-data')
    total_entradas = Financeiro.objects.filter(tipo='ENTRADA').aggregate(
        total=Sum('valor'))['total'] or 0
    total_saidas = Financeiro.objects.filter(tipo='SAIDA').aggregate(
        total=Sum('valor'))['total'] or 0
    saldo_final = total_entradas - total_saidas

    context = {
        'transacoes': transacoes,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_final': saldo_final,
        'financeiro_chart': build_finance_chart_data(limit=8),
    }
    return render(request, 'management/financeiro.html', context)


@permission_required('management.view_financeiro', raise_exception=True)
def financeiro_pdf(request):
    transacoes = Financeiro.objects.all().order_by('-data')
    total_entradas = Financeiro.objects.filter(tipo='ENTRADA').aggregate(
        total=Sum('valor'))['total'] or 0
    total_saidas = Financeiro.objects.filter(tipo='SAIDA').aggregate(
        total=Sum('valor'))['total'] or 0
    saldo_final = total_entradas - total_saidas

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Relatório Financeiro', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f'Total de Entradas: R$ {total_entradas:.2f}', styles['Normal']))
    elements.append(Paragraph(
        f'Total de Saídas: R$ {total_saidas:.2f}', styles['Normal']))
    elements.append(Paragraph(
        f'Saldo Final: R$ {saldo_final:.2f}', styles['Normal']))
    elements.append(Spacer(1, 18))

    data = [['Data', 'Descrição', 'Tipo', 'Valor']]
    for transacao in transacoes:
        tipo = 'Entrada' if transacao.tipo == 'ENTRADA' else 'Saída'
        data.append([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.descricao,
            tipo,
            f'R$ {transacao.valor:.2f}'
        ])

    data.append(['', '', 'Total Entradas', f'R$ {total_entradas:.2f}'])
    data.append(['', '', 'Total Saídas', f'R$ {total_saidas:.2f}'])
    data.append(['', '', 'Saldo Final', f'R$ {saldo_final:.2f}'])

    table = Table(data, colWidths=[70, 260, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 1), (-1, -4), colors.whitesmoke),
        ('BACKGROUND', (2, -3), (-1, -1), colors.lightgrey),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_financeiro.pdf"'
    return response


@permission_required('management.view_material', raise_exception=True)
def lista_estoque(request):
    materiais = Material.objects.all()
    materiais_baixo_estoque = materiais.filter(
        quantidade_atual__lte=F('quantidade_minima')
    ).order_by('nome')
    total_items = materiais.count()
    total_quantidade = materiais.aggregate(
        total=Sum('quantidade_atual'))['total'] or 0
    context = {
        'materiais': materiais,
        'materiais_baixo_estoque': materiais_baixo_estoque,
        'colaboradores_ativos': Medium.objects.filter(ativo=True).order_by('nome_completo'),
        'listas_compra_recent': ListaCompra.objects.select_related('responsavel').order_by('-data_criacao')[:5],
        'total_items': total_items,
        'total_quantidade': total_quantidade,
    }
    return render(request, 'management/estoque.html', context)


@permission_required('management.view_material', raise_exception=True)
def listas_compra(request):
    listas = ListaCompra.objects.select_related(
        'responsavel').prefetch_related('itens').order_by('-data_criacao')
    return render(request, 'management/listas_compra.html', {
        'listas_compra': listas,
    })


@permission_required('management.view_material', raise_exception=True)
def detalhe_lista_compra(request, pk):
    lista = get_object_or_404(
        ListaCompra.objects.select_related(
            'responsavel').prefetch_related('itens__material'),
        pk=pk,
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'status':
            novo_status = request.POST.get('status')
            status_validos = {valor for valor, _ in ListaCompra.STATUS_CHOICES}
            if novo_status in status_validos:
                lista.status = novo_status
                lista.save(update_fields=['status', 'data_atualizacao'])
                messages.success(
                    request, f'Lista #{lista.id} atualizada com sucesso.')
                return redirect('detalhe_lista_compra', pk=lista.id)
            messages.error(request, 'Status inválido para a lista de compra.')
        elif action == 'delete':
            lista_id = lista.id
            lista.delete()
            messages.success(
                request, f'Lista de compra #{lista_id} removida com sucesso.')
            return redirect('listas_compra')

    return render(request, 'management/detalhe_lista_compra.html', {
        'lista': lista,
        'status_choices': ListaCompra.STATUS_CHOICES,
    })


def _salvar_lista_compra(materiais_baixo_estoque, colaborador, request):
    lista_compra = ListaCompra.objects.create(
        responsavel=colaborador,
        status='GERADA',
    )

    itens_compra = []
    total_previsto = Decimal('0')

    for material in materiais_baixo_estoque:
        campo_valor = f'valor_item_{material.pk}'
        valor_bruto = request.POST.get(campo_valor, '')

        try:
            valor = parse_currency_input(valor_bruto)
        except (InvalidOperation, ValueError):
            lista_compra.delete()
            raise

        total_previsto += valor
        ListaCompraItem.objects.create(
            lista=lista_compra,
            material=material,
            material_nome=material.nome,
            categoria=material.categoria,
            quantidade_atual=material.quantidade_atual,
            quantidade_minima=material.quantidade_minima,
            unidade_medida=material.unidade_medida,
            valor_previsto=valor,
        )
        itens_compra.append({
            'material': material,
            'valor': valor,
        })

    lista_compra.total_previsto = total_previsto
    lista_compra.save(update_fields=['total_previsto', 'data_atualizacao'])
    return lista_compra, itens_compra


@permission_required('management.view_material', raise_exception=True)
@require_POST
def lista_compra_pdf(request):
    materiais_baixo_estoque = list(
        Material.objects.filter(quantidade_atual__lte=F(
            'quantidade_minima')).order_by('nome')
    )

    if not materiais_baixo_estoque:
        messages.warning(
            request, 'Não há itens com estoque baixo para gerar lista de compra.')
        return redirect('estoque')

    colaborador_id = request.POST.get('colaborador_responsavel')
    colaborador = Medium.objects.filter(pk=colaborador_id, ativo=True).first()
    if not colaborador:
        messages.error(request, 'Selecione um colaborador responsável válido.')
        return redirect('estoque')

    try:
        lista_compra, itens_compra = _salvar_lista_compra(
            materiais_baixo_estoque,
            colaborador,
            request,
        )
    except (InvalidOperation, ValueError):
        messages.error(
            request, 'Valor inválido informado em um dos itens da lista de compra.')
        return redirect('estoque')

    total_previsto = lista_compra.total_previsto

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(f'Lista de Compra #{lista_compra.id} - Estoque Baixo', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f'Responsável pela compra: {colaborador.nome_completo}', styles['Normal']))
    elements.append(
        Paragraph(f'Itens com estoque baixo: {len(itens_compra)}', styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [['Codigo', 'Material', 'Qtd. Atual', 'Qtd. Mínima',
             'Unidade', 'Valor Previsto (R$)']]
    for item in itens_compra:
        material = item['material']
        data.append([
            str(material.id),
            material.nome,
            str(material.quantidade_atual),
            str(material.quantidade_minima),
            material.unidade_medida,
            f'{item["valor"]:.2f}',
        ])

    data.append(['', '', '', '', 'Total Previsto', f'{total_previsto:.2f}'])

    table = Table(data, colWidths=[50, 145, 60, 60, 60, 115])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('BACKGROUND', (4, -1), (-1, -1), colors.lightgrey),
        ('ALIGN', (2, 1), (5, -1), 'RIGHT'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="lista_compra_{lista_compra.id}.pdf"'
    return response


@permission_required('management.view_material', raise_exception=True)
def estoque_pdf(request):
    materiais = Material.objects.all().order_by('nome')
    total_items = materiais.count()
    total_quantidade = materiais.aggregate(
        total=Sum('quantidade_atual'))['total'] or 0

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Relatório de Estoque', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(f'Itens no estoque: {total_items}', styles['Normal']))
    elements.append(
        Paragraph(f'Quantidade total: {total_quantidade}', styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [['Codigo', 'Material', 'Categoria', 'Qtd. Atual',
             'Qtd. Mínima', 'Unidade', 'Status']]
    for m in materiais:
        status = 'Estoque Baixo' if m.quantidade_atual <= m.quantidade_minima else 'Normal'
        data.append([
            str(m.id),
            m.nome,
            m.categoria or '-',
            str(m.quantidade_atual),
            str(m.quantidade_minima),
            m.unidade_medida,
            status,
        ])

    table = Table(data, colWidths=[45, 120, 85, 55, 55, 55, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('ALIGN', (3, 1), (5, -1), 'RIGHT'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_estoque.pdf"'
    return response


@permission_required('management.add_material', raise_exception=True)
def criar_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estoque')
    else:
        form = MaterialForm()
    return render(request, 'management/create_material.html', {'form': form})


@permission_required('management.change_material', raise_exception=True)
def editar_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('estoque')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'management/create_material.html', {'form': form, 'edit': True, 'material': material})


@permission_required('management.add_evento', raise_exception=True)
def criar_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_eventos')
    else:
        form = EventoForm()
    return render(request, 'management/create_evento.html', {'form': form})


@permission_required('management.change_evento', raise_exception=True)
def editar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect('lista_eventos')
    else:
        form = EventoForm(instance=evento)
    return render(request, 'management/create_evento.html', {'form': form, 'edit': True, 'evento': evento})


@permission_required('management.view_banho', raise_exception=True)
def lista_banhos(request):
    # filtros via querystring: tipo e entidade (nome da entidade)
    tipo = request.GET.get('tipo')
    entidade = request.GET.get('entidade')

    banhos = Banho.objects.select_related('medium').all()
    if tipo:
        banhos = banhos.filter(tipo=tipo)
    if entidade:
        banhos = banhos.filter(entidade__icontains=entidade)

    banhos = banhos.order_by('-data', '-horario')

    context = {
        'banhos': banhos,
        'tipo_choices': Banho.TIPO_BANHO,
        'current_tipo': tipo,
        'current_entidade': entidade,
    }
    return render(request, 'management/banhos.html', context)


@permission_required('management.add_banho', raise_exception=True)
def criar_banho(request):
    if request.method == 'POST':
        form = BanhoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_banhos')
    else:
        form = BanhoForm()
    return render(request, 'management/create_banho.html', {'form': form})


@permission_required('management.change_banho', raise_exception=True)
def editar_banho(request, pk):
    banho = get_object_or_404(Banho, pk=pk)
    if request.method == 'POST':
        form = BanhoForm(request.POST, instance=banho)
        if form.is_valid():
            form.save()
            return redirect('lista_banhos')
    else:
        form = BanhoForm(instance=banho)
    return render(request, 'management/create_banho.html', {'form': form, 'edit': True, 'banho': banho})


@permission_required('management.view_banho', raise_exception=True)
def banhos_pdf(request):
    banhos = Banho.objects.select_related(
        'medium').order_by('-data', '-horario')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Relatório de Banhos', styles['Title']))
    elements.append(Spacer(1, 12))

    data = [['Data', 'Horário', 'Título', 'Tipo', 'Responsável', 'Descrição']]
    for banho in banhos:
        horario = banho.horario.strftime('%H:%M') if banho.horario else '-'
        responsavel = banho.medium.nome_completo if banho.medium else '-'
        data.append([
            banho.data.strftime('%d/%m/%Y'),
            horario,
            banho.titulo,
            banho.get_tipo_display(),
            responsavel,
            Paragraph(banho.descricao or '-', styles['BodyText'])
        ])

    table = Table(data, colWidths=[60, 50, 120, 90, 90, 240])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_banhos.pdf"'
    return response


@permission_required('management.add_medium', raise_exception=True)
def criar_medium(request):
    if request.method == 'POST':
        form = MediumForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_membros')
    else:
        form = MediumForm()
    return render(request, 'management/create_medium.html', {'form': form})


@permission_required('management.change_medium', raise_exception=True)
def editar_medium(request, pk):
    membro = get_object_or_404(Medium, pk=pk)
    if request.method == 'POST':
        form = MediumForm(request.POST, instance=membro)
        if form.is_valid():
            form.save()
            return redirect('lista_membros')
    else:
        form = MediumForm(instance=membro)
    return render(request, 'management/create_medium.html', {'form': form, 'edit': True, 'membro': membro})


@permission_required('management.add_financeiro', raise_exception=True)
def criar_financeiro(request):
    if request.method == 'POST':
        form = FinanceiroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('financeiro')
    else:
        form = FinanceiroForm()
    return render(request, 'management/create_financeiro.html', {'form': form})


@permission_required('management.add_movimentacaoestoque', raise_exception=True)
def criar_movimentacao(request):
    if request.method == 'POST':
        form = MovimentacaoEstoqueForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estoque')
    else:
        form = MovimentacaoEstoqueForm()
    return render(request, 'management/create_movimentacao.html', {'form': form})


@permission_required('management.view_tarefa', raise_exception=True)
def lista_tarefas(request):
    # filtros via querystring: status, papel (função do colaborador) e pesquisa livre
    status = request.GET.get('status')
    papel = request.GET.get('papel')
    q = request.GET.get('q')

    tarefas = Tarefa.objects.select_related('medium').all()
    if status:
        tarefas = tarefas.filter(status=status)
    if papel:
        tarefas = tarefas.filter(medium__papel=papel)
    if q:
        tarefas = tarefas.filter(
            Q(titulo__icontains=q) | Q(descricao__icontains=q) | Q(
                medium__nome_completo__icontains=q)
        )

    tarefas = tarefas.order_by('-data_vencimento', 'status')

    context = {
        'tarefas': tarefas,
        'status_choices': Tarefa.STATUS_CHOICES,
        'papel_choices': Medium.ROLE_CHOICES,
        'current_status': status,
        'current_papel': papel,
        'q': q,
    }
    return render(request, 'management/tarefas.html', context)


@permission_required('management.view_tarefa', raise_exception=True)
def lista_tarefas_member(request, pk):
    membro = get_object_or_404(Medium, pk=pk)
    status = request.GET.get('status')
    papel = request.GET.get('papel')
    q = request.GET.get('q')

    tarefas = membro.tarefas.all()
    if status:
        tarefas = tarefas.filter(status=status)
    if papel:
        tarefas = tarefas.filter(medium__papel=papel)
    if q:
        tarefas = tarefas.filter(
            Q(titulo__icontains=q) | Q(descricao__icontains=q) | Q(
                medium__nome_completo__icontains=q)
        )

    tarefas = tarefas.order_by('-data_vencimento', 'status')

    context = {
        'tarefas': tarefas,
        'membro': membro,
        'status_choices': Tarefa.STATUS_CHOICES,
        'papel_choices': Medium.ROLE_CHOICES,
        'current_status': status,
        'current_papel': papel,
        'q': q,
    }
    return render(request, 'management/tarefas.html', context)


@permission_required('management.add_tarefa', raise_exception=True)
def criar_tarefa(request, pk=None):
    membro = get_object_or_404(Medium, pk=pk) if pk else None

    if request.method == 'POST':
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            if membro and not tarefa.medium_id:
                tarefa.medium = membro
            tarefa.save()
            return redirect('lista_tarefas_member', pk=tarefa.medium.pk) if tarefa.medium else redirect('lista_tarefas')
    else:
        form = TarefaForm(initial={'medium': membro} if membro else None)

    return render(request, 'management/create_tarefa.html', {'form': form, 'edit': False, 'membro': membro})


@permission_required('management.change_tarefa', raise_exception=True)
def editar_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == 'POST':
        form = TarefaForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            return redirect('lista_tarefas_member', pk=tarefa.medium.pk)
    else:
        form = TarefaForm(instance=tarefa)

    return render(request, 'management/create_tarefa.html', {'form': form, 'edit': True, 'tarefa': tarefa})


@permission_required('management.view_tarefa', raise_exception=True)
def tarefas_pdf(request):
    membro_id = request.GET.get('membro')
    status = request.GET.get('status')
    papel = request.GET.get('papel')
    q = request.GET.get('q')

    tarefas = Tarefa.objects.select_related('medium').all()
    if membro_id:
        tarefas = tarefas.filter(medium_id=membro_id)
    if status:
        tarefas = tarefas.filter(status=status)
    if papel:
        tarefas = tarefas.filter(medium__papel=papel)
    if q:
        tarefas = tarefas.filter(
            Q(titulo__icontains=q) | Q(descricao__icontains=q) | Q(
                medium__nome_completo__icontains=q)
        )
    tarefas = tarefas.order_by('-data_vencimento', 'status')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Relatório de Tarefas', styles['Title']))
    elements.append(Spacer(1, 12))

    data = [['Colaborador', 'Tarefa', 'Vencimento', 'Status', 'Descrição']]
    for tarefa in tarefas:
        vencimento = tarefa.data_vencimento.strftime(
            '%d/%m/%Y') if tarefa.data_vencimento else '-'
        data.append([
            tarefa.medium.nome_completo,
            tarefa.titulo,
            vencimento,
            tarefa.get_status_display(),
            tarefa.descricao or '-'
        ])

    table = Table(data, colWidths=[120, 120, 70, 90, 140])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_tarefas.pdf"'
    return response
