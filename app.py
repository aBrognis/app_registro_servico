from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('SERVICES.DB')
    conn.row_factory = sqlite3.Row
    return conn

# Criar a tabela se não existir
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS SERVICES (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            REF TEXT,
            QTDE INTEGER,
            PRECO REAL,
            LINHA REAL,
            TOTAL REAL,
            DATA TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Rota principal
@app.route('/')
def home():
    return redirect(url_for('combined'))

# Rota para adicionar serviço
@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        ref = request.form.get('ref')
        qtde = request.form.get('qtde')
        preco = request.form.get('preco')
        linha = request.form.get('linha')

        if not ref or not qtde or not preco or not linha:
            flash('Por favor, preencha todos os campos.')
            return redirect(url_for('add'))
        
        preco = preco.replace(",", ".")
        linha = linha.replace(",", ".")
        total = int(qtde) * (float(preco) + float(linha))
        data = datetime.now().strftime('%Y-%m-%d')

        conn = get_db_connection()
        conn.execute('INSERT INTO SERVICES (REF, QTDE, PRECO, LINHA, TOTAL, DATA) VALUES (?, ?, ?, ?, ?, ?)',
                     (ref, qtde, float(preco), float(linha), total, data))
        conn.commit()
        conn.close()
        flash('Serviço adicionado com sucesso!')
        return redirect(url_for('combined'))
    return render_template('add.html')

# Rota para visualizar e pesquisar serviços
@app.route('/combined', methods=['GET', 'POST'])
def combined():
    create_table()
    services = []
    if request.method == 'POST':
        ref = request.form.get('ref')
        date_start = request.form.get('date_start')
        date_end = request.form.get('date_end')
        query = 'SELECT * FROM SERVICES WHERE 1=1'
        parameters = []

        if ref:
            query += ' AND REF = ?'
            parameters.append(ref)
        if date_start and date_end:
            query += ' AND DATA BETWEEN ? AND ?'
            parameters.append(date_start)
            parameters.append(date_end)

        conn = get_db_connection()
        services = conn.execute(query, parameters).fetchall()
        conn.close()
    else:
        conn = get_db_connection()
        services = conn.execute('SELECT * FROM SERVICES').fetchall()
        conn.close()

    return render_template('combined.html', services=services)

# Rota para editar serviço
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit(id):
    create_table()
    conn = get_db_connection()
    service = conn.execute('SELECT * FROM SERVICES WHERE ID = ?', (id,)).fetchone()

    if request.method == 'POST':
        ref = request.form['ref']
        qtde = request.form['qtde']
        preco = request.form['preco']
        linha = request.form['linha']
        
        if not ref or not qtde or not preco or not linha:
            flash('Por favor, preencha todos os campos.')
            return redirect(url_for('edit', id=id))

        preco = preco.replace(",", ".")
        linha = linha.replace(",", ".")
        total = int(qtde) * (float(preco) + float(linha))
        data = datetime.now().strftime('%Y-%m-%d')

        conn.execute('UPDATE SERVICES SET REF = ?, QTDE = ?, PRECO = ?, LINHA = ?, TOTAL = ?, DATA = ? WHERE ID = ?',
                     (ref, qtde, float(preco), float(linha), total, data, id))
        conn.commit()
        conn.close()
        flash('Serviço atualizado com sucesso!')
        return redirect(url_for('combined'))

    conn.close()
    return render_template('edit.html', service=service)

# Rota para deletar um serviço
@app.route('/delete/<int:id>')
def delete(id):
    create_table()
    conn = get_db_connection()
    conn.execute('DELETE FROM SERVICES WHERE ID = ?', (id,))
    conn.commit()
    conn.close()
    flash('Serviço deletado com sucesso!')
    return redirect(url_for('combined'))

# Rota para gerar PDF
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf_route():
    title = request.form.get('title', 'Relatório de Serviços')
    if not title.strip():
        title = "Relatório de Serviços"

    conn = get_db_connection()
    services = conn.execute('SELECT * FROM SERVICES').fetchall()
    conn.close()

    return generate_pdf(services, title)

# Função para gerar o PDF
def generate_pdf(services, title):
    pdf_file = f"{title.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    elements = []
    style = getSampleStyleSheet()
    title_style = style["Title"]
    title_style.alignment = 1
    bold_style = ParagraphStyle(name='Bold', fontSize=12, leading=14, fontName='Helvetica-Bold')

    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))

    data = [["REF", "QTDE", "PREÇO", "LINHA", "TOTAL"]]
    total_qtde = 0
    total_valor = 0

    for service in services:
        ref, qtde, preco, linha, total = service['REF'], service['QTDE'], service['PRECO'], service['LINHA'], service['TOTAL']
        total_qtde += int(qtde)
        total_valor += total
        data.append([ref, qtde, f"R$ {preco:,.2f}", f"R$ {linha:,.2f}", f"R$ {total:,.2f}"])
    
    summary_row = ["", total_qtde, "", "", f"R$ {total_valor:,.2f}"]
    data.append(summary_row)

    table = Table(data, colWidths=[50, 100, 100, 100, 100])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgreen),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"TOTAL DE PEÇAS: {total_qtde}", bold_style))
    elements.append(Paragraph(f"TOTAL A PAGAR: R$ {total_valor:,.2f}", bold_style))

    doc.build(elements)
    return send_file(pdf_file, as_attachment=True)

# Iniciar a aplicação
if __name__ == '__main__':
    app.run(debug=True)
