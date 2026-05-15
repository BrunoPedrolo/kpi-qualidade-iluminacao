from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import base64
import requests
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

GITHUB_TOKEN  = os.environ.get('GITHUB_TOKEN', '')
GITHUB_USER   = 'BrunoPedrolo'
GITHUB_REPO   = 'kpi-qualidade-iluminacao'
GITHUB_FILE   = 'dados.json'
GITHUB_BRANCH = 'main'

META     = 21
META_MIN = 18

def get_dados_github():
    url = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        return json.loads(content), data['sha']
    return {'dias': {}, 'ultima_atualizacao': ''}, None

def salvar_dados_github(dados, sha=None):
    url = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
    content = base64.b64encode(json.dumps(dados, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
    payload = {
        'message': f'Atualização KPI - {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        'content': content,
        'branch': GITHUB_BRANCH
    }
    if sha:
        payload['sha'] = sha
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]

def processar_xlsx(file):
    df = pd.read_excel(file)

    # Filtrar pelo item de aprovação
    aprovacao = df[df['Item'] == 'Aprovação geral da etapa inspecionada.'].copy()
    aprovacao['Data inicial'] = pd.to_datetime(aprovacao['Data inicial'], dayfirst=True, errors='coerce')
    aprovacao['Data'] = aprovacao['Data inicial'].dt.strftime('%d/%m')

    # Identificar reprovados (checklists com algum "Não")
    nao_ids = set(df[df['Resposta'] == 'Não']['Código da avaliação'].unique())
    aprovacao['resultado'] = aprovacao['Código da avaliação'].apply(
        lambda x: 'rep' if x in nao_ids else 'apr'
    )

    # Juntar com executor
    executores = df[df['Item'] == 'Executor'][['Código da avaliação', 'Resposta']].copy()
    executores.columns = ['Código da avaliação', 'Inspetor']
    base = aprovacao.merge(executores, on='Código da avaliação', how='left')

    # Juntar com tipo de unidade
    tipos = df[['Código da avaliação', 'Tipo de Unidade']].drop_duplicates()
    base = base.merge(tipos, on='Código da avaliação', how='left')

    # Agrupar por inspetor e data
    resultado = {}
    for (inspetor, data), grupo in base.groupby(['Inspetor', 'Data']):
        if pd.isna(inspetor):
            continue
        total  = len(grupo)
        apr    = int((grupo['resultado'] == 'apr').sum())
        rep    = int((grupo['resultado'] == 'rep').sum())
        pot    = int((grupo['Tipo de Unidade'] == 'Iluminação Potência').sum())
        tub    = int((grupo['Tipo de Unidade'] == 'Iluminação Tubular').sum())
        pct    = round(total / META * 100, 1)

        if data not in resultado:
            resultado[data] = {}

        resultado[data][inspetor] = {
            't': total, 'apr': apr, 'rep': rep,
            'pot': pot, 'tub': tub, 'pct': pct
        }

    return resultado

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

@app.route('/dados', methods=['GET'])
def get_dados():
    dados, _ = get_dados_github()
    return jsonify(dados)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if not file.filename.endswith('.xlsx'):
        return jsonify({'erro': 'Apenas arquivos .xlsx são aceitos'}), 400

    try:
        novos = processar_xlsx(file)
        dados, sha = get_dados_github()

        if 'dias' not in dados:
            dados['dias'] = {}

        # Mesclar novos dados com existentes
        for data, inspetores in novos.items():
            if data not in dados['dias']:
                dados['dias'][data] = {}
            for insp, vals in inspetores.items():
                dados['dias'][data][insp] = vals

        dados['ultima_atualizacao'] = datetime.now().strftime('%d/%m/%Y %H:%M')

        ok = salvar_dados_github(dados, sha)
        if not ok:
            return jsonify({'erro': 'Erro ao salvar no GitHub'}), 500

        dias_processados = list(novos.keys())
        total_insp = sum(
            v['t'] for d in novos.values() for v in d.values()
        )

        return jsonify({
            'sucesso': True,
            'dias_processados': dias_processados,
            'total_inspecoes': total_insp,
            'mensagem': f'{len(dias_processados)} dia(s) processado(s) com {total_insp} inspeções'
        })

    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
