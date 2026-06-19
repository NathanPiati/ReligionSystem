from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Medium, Evento, Financeiro, Presenca, Material, Tarefa, Banho
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from .forms import MediumForm, EventoForm, FinanceiroForm, MaterialForm, MovimentacaoEstoqueForm, TarefaForm, BanhoForm
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


@login_required
def dashboard(request):
    total_membros = Medium.objects.filter(ativo=True).count()
    proximos_eventos = Evento.objects.all().order_by('data')[:5]
    saldo = Financeiro.objects.filter(tipo='ENTRADA').aggregate(Sum('valor'))[
        'valor__sum'] or 0
    despesas = Financeiro.objects.filter(tipo='SAIDA').aggregate(Sum('valor'))[
        'valor__sum'] or 0
    saldo_final = saldo - despesas

    context = {
        'total_membros': total_membros,
        'proximos_eventos': proximos_eventos,
        'saldo_final': saldo_final,
    }
    return render(request, 'management/dashboard.html', context)


@login_required
def lista_membros(request):
    membros = Medium.objects.all()
    return render(request, 'management/membros.html', {'membros': membros})


@login_required
def lista_eventos(request):
    eventos = Evento.objects.all().order_by('-data')
    return render(request, 'management/eventos.html', {'eventos': eventos})


@login_required
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
    }
    return render(request, 'management/financeiro.html', context)


@login_required
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


@login_required
def lista_estoque(request):
    materiais = Material.objects.all()
    total_items = materiais.count()
    total_quantidade = materiais.aggregate(
        total=Sum('quantidade_atual'))['total'] or 0
    context = {
        'materiais': materiais,
        'total_items': total_items,
        'total_quantidade': total_quantidade,
    }
    return render(request, 'management/estoque.html', context)


@login_required
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

    data = [['Material', 'Categoria', 'Qtd. Atual',
             'Qtd. Mínima', 'Unidade', 'Status']]
    for m in materiais:
        status = 'Estoque Baixo' if m.quantidade_atual <= m.quantidade_minima else 'Normal'
        data.append([
            m.nome,
            m.categoria or '-',
            str(m.quantidade_atual),
            str(m.quantidade_minima),
            m.unidade_medida,
            status,
        ])

    table = Table(data, colWidths=[140, 90, 60, 60, 60, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_estoque.pdf"'
    return response


@login_required
def criar_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estoque')
    else:
        form = MaterialForm()
    return render(request, 'management/create_material.html', {'form': form})


@login_required
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


@login_required
def criar_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_eventos')
    else:
        form = EventoForm()
    return render(request, 'management/create_evento.html', {'form': form})


@login_required
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


@login_required
def criar_banho(request):
    if request.method == 'POST':
        form = BanhoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_banhos')
    else:
        form = BanhoForm()
    return render(request, 'management/create_banho.html', {'form': form})


@login_required
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


@login_required
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


@login_required
def criar_medium(request):
    if request.method == 'POST':
        form = MediumForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_membros')
    else:
        form = MediumForm()
    return render(request, 'management/create_medium.html', {'form': form})


@login_required
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


@login_required
def criar_financeiro(request):
    if request.method == 'POST':
        form = FinanceiroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('financeiro')
    else:
        form = FinanceiroForm()
    return render(request, 'management/create_financeiro.html', {'form': form})


@login_required
def criar_movimentacao(request):
    if request.method == 'POST':
        form = MovimentacaoEstoqueForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estoque')
    else:
        form = MovimentacaoEstoqueForm()
    return render(request, 'management/create_movimentacao.html', {'form': form})


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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
