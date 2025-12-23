import streamlit as st
import pandas as pd
from datetime import datetime
import io
from streamlit_gsheets import GSheetsConnection

# --- Configuração da Página ---
st.set_page_config(page_title="Alocação de Salas", layout="wide")

st.title("🎓 Sistema de Alocação de Salas Inteligente (Conectado ao Google Sheets)")

# --- LISTA DE RECURSOS DISPONÍVEIS ---
OPCOES_RECURSOS = ["Projetor", "Quadro", "Laboratório", "Computadores", "Mesas", "Cadeiras"]

# --- CONEXÃO COM GOOGLE SHEETS ---
# Cria a conexão usando os segredos configurados
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para carregar dados (cache de 2 segundos para garantir atualização rápida)
def carregar_dados():
    try:
        return conn.read(worksheet="Salas", ttl=2)
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return pd.DataFrame(columns=['Código', 'Descrição', 'Ambiente', 'Capacidade', 'Recursos'])

# Função para SALVAR dados no Google Sheets
def salvar_no_gsheets(df):
    try:
        conn.update(worksheet="Salas", data=df)
        st.toast("✅ Alterações salvas no Google Sheets!", icon="☁️")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- 0. Inicialização da "Memória" ---
# Se não tiver carregado ainda, busca do Sheets
if 'df_salas' not in st.session_state:
    st.session_state.df_salas = carregar_dados()

# --- FUNÇÕES DE POP-UP (DIALOGS) ---

@st.dialog("➕ Adicionar Nova Sala")
def modal_adicionar_sala():
    with st.form("form_add_sala"):
        cod = st.text_input("Código (Ex: A101)")
        desc = st.text_input("Descrição")
        amb = st.selectbox("Ambiente", ["Sala de Aula", "Laboratório", "Auditório", "Informática"])
        cap = st.number_input("Capacidade", min_value=1, step=1)
        
        st.markdown("**Recursos Disponíveis:**")
        c1, c2, c3 = st.columns(3)
        recursos_selecionados = []
        for i, opcao in enumerate(OPCOES_RECURSOS):
            with [c1, c2, c3][i % 3]:
                if st.checkbox(opcao, key=f"add_{opcao}"):
                    recursos_selecionados.append(opcao)
        
        st.markdown("---")
        if st.form_submit_button("💾 Salvar Sala", type="primary"):
            if cod and desc: 
                rec_str = ", ".join(recursos_selecionados)
                nova_linha = pd.DataFrame([{
                    'Código': cod, 'Descrição': desc, 'Ambiente': amb, 
                    'Capacidade': cap, 'Recursos': rec_str
                }])
                # Atualiza memória local
                st.session_state.df_salas = pd.concat([st.session_state.df_salas, nova_linha], ignore_index=True)
                # SALVA NA NUVEM
                salvar_no_gsheets(st.session_state.df_salas)
                st.rerun()
            else:
                st.error("Preencha Código e Descrição.")

@st.dialog("✏️ Editar Sala")
def modal_editar_sala(index_selecionado):
    sala_atual = st.session_state.df_salas.iloc[index_selecionado]
    
    col1, col2 = st.columns(2)
    novo_cod = col1.text_input("Código", value=sala_atual['Código'])
    novo_cap = col2.number_input("Capacidade", value=int(sala_atual['Capacidade']), min_value=1)
    nova_desc = st.text_input("Descrição", value=sala_atual['Descrição'])
    
    lista_ambientes = ["Sala de Aula", "Laboratório", "Auditório", "Informática"]
    idx_amb = lista_ambientes.index(sala_atual['Ambiente']) if sala_atual['Ambiente'] in lista_ambientes else 0
    novo_amb = st.selectbox("Ambiente", lista_ambientes, index=idx_amb)
    
    st.markdown("**Recursos:**")
    recursos_atuais = [r.strip() for r in str(sala_atual['Recursos']).split(',')]
    novos_recursos = []
    c1, c2, c3 = st.columns(3)
    for i, opcao in enumerate(OPCOES_RECURSOS):
        with [c1, c2, c3][i % 3]:
            if st.checkbox(opcao, value=(opcao in recursos_atuais), key=f"edit_{opcao}"):
                novos_recursos.append(opcao)

    st.markdown("---")
    c_salvar, c_cancel = st.columns(2)
    
    if c_salvar.button("💾 Salvar Alterações", type="primary"):
        st.session_state.df_salas.at[index_selecionado, 'Código'] = novo_cod
        st.session_state.df_salas.at[index_selecionado, 'Descrição'] = nova_desc
        st.session_state.df_salas.at[index_selecionado, 'Ambiente'] = novo_amb
        st.session_state.df_salas.at[index_selecionado, 'Capacidade'] = novo_cap
        st.session_state.df_salas.at[index_selecionado, 'Recursos'] = ", ".join(novos_recursos)
        
        # SALVA NA NUVEM
        salvar_no_gsheets(st.session_state.df_salas)
        st.rerun()

    if c_cancel.button("❌ Cancelar"):
        st.rerun()

@st.dialog("🗑️ Confirmar Exclusão")
def modal_excluir_sala(index_selecionado):
    sala_atual = st.session_state.df_salas.iloc[index_selecionado]
    st.warning(f"Excluir **{sala_atual['Código']}** permanentemente?")
    
    col_sim, col_nao = st.columns(2)
    if col_sim.button("Sim, Excluir", type="primary"):
        st.session_state.df_salas = st.session_state.df_salas.drop(index_selecionado).reset_index(drop=True)
        # SALVA NA NUVEM
        salvar_no_gsheets(st.session_state.df_salas)
        st.rerun()
    
    if col_nao.button("Cancelar"):
        st.rerun()

# --- LÓGICA DE ALOCAÇÃO (MANTIDA) ---
def verificar_conflito_horario(t1_inicio, t1_fim, t2_inicio, t2_fim):
    return max(t1_inicio, t2_inicio) < min(t1_fim, t2_fim)

def alocar_salas(df_turmas, df_salas):
    # (Mantive a mesma lógica da sua versão anterior)
    alocacoes = []
    ocupacao_salas = {codigo: [] for codigo in df_salas['Código'].unique()}
    
    for index, row in df_turmas.iterrows():
        raw_dias = str(row['Dia']).replace('/', ',').replace(' e ', ',').replace(' E ', ',')
        lista_dias = [d.strip() for d in raw_dias.split(',')]

        for dia_atual in lista_dias:
            if not dia_atual: continue
            
            turma_alocada = False
            necessidade = row.get('Necessidades', None)
            qtd_alunos = row['Qtd_Alunos']
            
            try:
                inicio = pd.to_datetime(row['Inicio'], format='%H:%M').time()
                fim = pd.to_datetime(row['Fim'], format='%H:%M').time()
            except:
                inicio = pd.to_datetime(str(row['Inicio'])).time()
                fim = pd.to_datetime(str(row['Fim'])).time()

            candidatas = df_salas[df_salas['Capacidade'] >= qtd_alunos].copy()
            candidatas = candidatas.sort_values(by='Capacidade')
            
            for idx_sala, sala in candidatas.iterrows():
                codigo_sala = sala['Código']
                recursos_sala = str(sala['Recursos']) + " " + str(sala['Ambiente'])
                
                if pd.notna(necessidade) and necessidade != "":
                    if necessidade.lower() not in recursos_sala.lower():
                        continue 

                conflito = False
                if codigo_sala in ocupacao_salas:
                    for agendamento in ocupacao_salas[codigo_sala]:
                        if agendamento['dia'] == dia_atual:
                            if verificar_conflito_horario(inicio, fim, agendamento['inicio'], agendamento['fim']):
                                conflito = True
                                break
                
                if not conflito:
                    ocupacao_salas[codigo_sala].append({'dia': dia_atual, 'inicio': inicio, 'fim': fim})
                    alocacoes.append({
                        'Cód. Matéria': row['Codigo'], 'Disciplina': row['Nome'], 'Professor': row['Professor'],
                        'Qtd_Alunos': qtd_alunos, 'Sala Alocada': f"{sala['Código']} - {sala['Ambiente']}",
                        'Capacidade': sala['Capacidade'], 'Ocupação': f"{(qtd_alunos/sala['Capacidade'])*100:.0f}%",
                        'Dia': dia_atual, 'Horário': f"{row['Inicio']} - {row['Fim']}", 'Status': 'Sucesso'
                    })
                    turma_alocada = True
                    break 
            
            if not turma_alocada:
                alocacoes.append({
                    'Cód. Matéria': row['Codigo'], 'Disciplina': row['Nome'], 'Professor': row['Professor'],
                    'Qtd_Alunos': qtd_alunos, 'Sala Alocada': 'NÃO ALOCADA', 'Capacidade': '-',
                    'Ocupação': '-', 'Dia': dia_atual, 'Horário': f"{row['Inicio']} - {row['Fim']}", 'Status': 'Erro: Sem sala compatível'
                })
    return pd.DataFrame(alocacoes)

# --- LAYOUT PRINCIPAL ---
col1, col2 = st.columns([1.2, 1.5], gap="large")

with col1:
    st.subheader("1. Gerenciar Salas (Google Sheets)")
    
    # Botão para recarregar manualmente do Google Sheets
    if st.button("🔄 Recarregar Dados da Nuvem"):
        st.session_state.df_salas = carregar_dados()
        st.rerun()

    event = st.dataframe(st.session_state.df_salas, on_select="rerun", selection_mode="single-row", use_container_width=True, hide_index=True)
    
    if st.button("➕ Adicionar Sala", use_container_width=True):
        modal_adicionar_sala()

    st.write("") 
    col_btn_edit, col_btn_del = st.columns(2)
    
    linhas = event.selection.rows
    if linhas:
        idx = linhas[0]
        if col_btn_edit.button("✏️ Editar", use_container_width=True): modal_editar_sala(idx)
        if col_btn_del.button("🗑️ Excluir", type="primary", use_container_width=True): modal_excluir_sala(idx)
    else:
        col_btn_edit.button("✏️ Editar", disabled=True, use_container_width=True)
        col_btn_del.button("🗑️ Excluir", disabled=True, use_container_width=True)

with col2:
    st.subheader("2. Upload de Turmas")
    with st.expander("📝 Baixar Modelo de Turmas"):
        # (Código de download do modelo mantido igual, omitido para economizar espaço mas deve estar aqui)
        # Se quiser que eu repita o bloco do download me avise, mas é o mesmo do anterior.
        st.info("Use o modelo padrão para garantir a importação.")
        
    upload_arquivo = st.file_uploader("Subir arquivo Excel das Matérias", type=['xlsx'])
    if upload_arquivo:
        try:
            df_turmas = pd.read_excel(upload_arquivo)
            if st.button("🚀 Processar Alocação", type="primary"):
                # Validação e Processamento (Mantidos)
                colunas_necessarias = ['Codigo', 'Nome', 'Professor', 'Qtd_Alunos', 'Inicio', 'Fim', 'Dia']
                if all(col in df_turmas.columns for col in colunas_necessarias):
                    resultado = alocar_salas(df_turmas, st.session_state.df_salas)
                    st.divider()
                    st.subheader("3. Resultados")
                    # (Exibição dos resultados mantida)
                    st.dataframe(resultado, use_container_width=True, hide_index=True)
                else:
                    st.error("Colunas incorretas.")
        except Exception as e:
            st.error(f"Erro: {e}")
