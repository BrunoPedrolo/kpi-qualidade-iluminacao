from flask import Flask, request, jsonify, redirect, send_file
from flask_cors import CORS
import pandas as pd
import json
import base64
import requests
from datetime import datetime
import os
import io

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

DASHBOARD_URL = 'https://brunopedrolo.github.io/kpi-qualidade-iluminacao/'

@app.route('/', methods=['GET'])
def index():
    return redirect(DASHBOARD_URL)

@app.route('/upload-page', methods=['GET'])
def upload_page():
    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Upload · KPI Iluminação</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{--green:#1a9e3f;--green-dark:#146b2a;--green-light:#e8f5ec;--border:#d4edda;--text:#1a2e1f;--muted:#5a7a62;--white:#fff;--font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace}
*{box-sizing:border-box;margin:0;padding:0}
html{background:#f4faf6;color:var(--text);font-family:var(--font);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:var(--white);border:1px solid var(--border);border-radius:12px;padding:32px;width:100%;max-width:480px;border-top:4px solid var(--green)}
.header{text-align:center;margin-bottom:28px}
.header h1{font-size:18px;font-weight:600;color:var(--green-dark);margin-bottom:4px}
.header p{font-size:12px;color:var(--muted);font-family:var(--mono)}
.drop-zone{border:2px dashed var(--border);border-radius:8px;padding:32px;text-align:center;cursor:pointer;background:var(--green-light);transition:all .2s;margin-bottom:12px}
.drop-zone:hover,.drop-zone.drag{border-color:var(--green);background:#d4edda}
.dicon{font-size:36px;margin-bottom:8px}
.drop-zone p{font-size:13px;color:var(--muted);font-family:var(--mono)}
.drop-zone strong{color:var(--green-dark)}
input[type=file]{display:none}
.file-name{font-size:12px;color:var(--green-dark);font-family:var(--mono);text-align:center;margin-bottom:12px;min-height:18px}
.btn{width:100%;background:var(--green);color:#fff;border:none;border-radius:8px;padding:13px;font-size:14px;font-weight:600;cursor:pointer;font-family:var(--font)}
.btn:hover{background:var(--green-dark)}
.btn:disabled{background:#aaa;cursor:not-allowed}
.result{margin-top:14px;padding:12px 16px;border-radius:8px;font-size:12px;font-family:var(--mono);display:none}
.ok{background:#e8f5ec;color:#146b2a;border:1px solid #b7dfc4}
.err{background:#fdecea;color:#8b1a1a;border:1px solid #f5b8b8}
.back{display:block;text-align:center;margin-top:16px;font-size:12px;color:var(--green);font-family:var(--mono);text-decoration:none}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>⬆ Novo upload</h1>
    <p>KPI · Qualidade · Iluminação · Zagonel</p>
  </div>
  <div class="drop-zone" id="dz" onclick="document.getElementById('fi').click()">
    <div class="dicon">📄</div>
    <p>Clique ou arraste o arquivo aqui</p>
    <p><strong>.xlsx</strong> exportado do sistema</p>
  </div>
  <input type="file" id="fi" accept=".xlsx"/>
  <div class="file-name" id="fn"></div>
  <button class="btn" id="btn" disabled onclick="enviar()">Selecione um arquivo</button>
  <div class="result" id="res"></div>
  <a class="back" href="https://brunopedrolo.github.io/kpi-qualidade-iluminacao/">← Voltar ao dashboard</a>
</div>
<script>
let file=null;
const dz=document.getElementById('dz'),fi=document.getElementById('fi');
const btn=document.getElementById('btn'),fn=document.getElementById('fn'),res=document.getElementById('res');
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('drag')});
dz.addEventListener('dragleave',()=>dz.classList.remove('drag'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('drag');const f=e.dataTransfer.files[0];if(f&&f.name.endsWith('.xlsx'))set(f)});
fi.addEventListener('change',()=>{if(fi.files[0])set(fi.files[0])});
function set(f){file=f;fn.textContent='📄 '+f.name;btn.disabled=false;btn.textContent='Enviar dados';res.style.display='none'}
async function enviar(){
  if(!file)return;
  btn.disabled=true;btn.innerHTML='<span class="spinner"></span>Processando...';res.style.display='none';
  const form=new FormData();form.append('file',file);
  try{
    const r=await fetch('/upload',{method:'POST',body:form});
    const j=await r.json();
    if(r.ok&&j.sucesso){
      res.className='result ok';res.innerHTML='✅ '+j.mensagem+'<br>Dias: '+j.dias_processados.join(', ');
      btn.textContent='✓ Enviado!';
    }else{
      res.className='result err';res.innerHTML='❌ '+(j.erro||'Erro ao processar');
      btn.disabled=false;btn.textContent='Tentar novamente';
    }
  }catch(e){
    res.className='result err';res.innerHTML='❌ Erro de conexão. Tente novamente.';
    btn.disabled=false;btn.textContent='Tentar novamente';
  }
  res.style.display='block';
}
</script>
</body>
</html>"""
    return html, 200, {'Content-Type': 'text/html'}

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
    df.columns = df.columns.str.strip()

    # Filtrar pelo item de aprovação
    aprovacao = df[df['Item'].astype(str).str.contains('Aprovação geral', case=False, na=False)].copy()
    if len(aprovacao) == 0:
        return {}

    aprovacao['Data inicial'] = pd.to_datetime(aprovacao['Data inicial'], dayfirst=True, errors='coerce')
    aprovacao['Data'] = aprovacao['Data inicial'].dt.strftime('%d/%m')

    # Identificar reprovados
    nao_ids = set(df[df['Resposta'].astype(str).str.strip() == 'Não']['Código da avaliação'].unique())
    aprovacao['resultado'] = aprovacao['Código da avaliação'].apply(
        lambda x: 'rep' if x in nao_ids else 'apr'
    )

    # Juntar com executor
    executores = df[df['Item'].astype(str).str.contains('Executor', case=False, na=False)][['Código da avaliação', 'Resposta']].copy()
    executores.columns = ['Código da avaliação', 'Inspetor']
    base = aprovacao.merge(executores, on='Código da avaliação', how='left')

    # Juntar com tipo de unidade com segurança
    tem_tipo = 'Tipo de Unidade' in df.columns
    if tem_tipo:
        try:
            tipos = df[['Código da avaliação', 'Tipo de Unidade']].drop_duplicates()
            base = base.merge(tipos, on='Código da avaliação', how='left')
        except Exception:
            tem_tipo = False

    if not tem_tipo or 'Tipo de Unidade' not in base.columns:
        base['Tipo de Unidade'] = ''

    base['Tipo de Unidade'] = base['Tipo de Unidade'].fillna('')

    # Agrupar por inspetor e data
    resultado = {}
    for (inspetor, data), grupo in base.groupby(['Inspetor', 'Data']):
        if pd.isna(inspetor):
            continue
        total = len(grupo)
        apr   = int((grupo['resultado'] == 'apr').sum())
        rep   = int((grupo['resultado'] == 'rep').sum())
        try:
            pot = int((grupo['Tipo de Unidade'] == 'Iluminação Potência').sum())
            tub = int((grupo['Tipo de Unidade'] == 'Iluminação Tubular').sum())
        except Exception:
            pot = 0
            tub = 0
        pct = round(total / META * 100, 1)

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
