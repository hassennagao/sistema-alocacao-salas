import streamlit as st
import pandas as pd
from datetime import datetime
import io  # Necessário para criar o arquivo Excel na memória

# --- Configuração da Página ---
st.set_page_config(page_title="Alocação de Salas", layout="wide")

st.title("🎓 Sistema de Alocação de Salas Inteligente")

# --- LISTA DE RECURSOS DISPONÍVEIS ---
OPCOES_RECURSOS = ["Projetor", "Quadro", "Laboratório", "Computadores", "Mesas", "Cadeiras"]

# --- 0. Inicialização da "Memória" ---
if 'df_salas' not in st.session_state:
    data_padrao = {
        'Código': [
            'PG-01', 'PG-02', 'PG-03', 'PGMec', 'PG-04', 
            'LVR2', 'PG-06', 'PG-07', 'PG-11', 'PG-12', 
            'PG-14', 'PG-15', 'PG-16', 'PG-17'
        ],
        'Descrição': [
            'Sala de Aula Mecânica - 01', 'Laboratório de Tribologia', 'Sala de Aula Mecânica - 03', 'Sala de Aula Pós Graduação', 'Sala de Aula Mecânica - 04',
            'Laboratório de Vibrações', 'Sala de Aula Mecânica - 06', 'Sala de Aula Mecânica - 07', 'Sala de Aula Mecânica - 11', 'Laboratório de Experimentação Numérica',
            'Laboratório de Impressão 3D', 'Sala de Aula Mecânica - 15', 'Sala de Professores', 'Micromechanical Testing Laboratory'
        ],
        'Ambiente': [
            'Sala de Aula', 'Laboratório', 'Sala de Aula', 'Sala de Aula', 'Sala de Aula',
            'Laboratório', 'Sala de Aula', 'Sala de Aula', 'Sala de Aula', 'Laboratório',
            'Laboratório', 'Sala de Aula', 'Laboratório', 'Laboratório'
        ],
        'Capacidade': [
            50, 15, 40, 20, 50,
            10, 40, 50, 40, 50,
            15, 50, 5, 10
        ],
        'Recursos': [
            'Projetor, Quadro, Mesas, Cadeiras', 'Quadro', 'Projetor, Quadro, Mesas, Cadeiras', 'Projetor, Quadro, Mesas, Cadeiras', 'Projetor, Quadro, Mesas, Cadeiras',
            'Quadro', 'Projetor, Quadro, Mesas, Cadeiras', 'Projetor, Quadro, Mesas, Cadeiras', 'Projetor, Quadro, Mesas, Cadeiras', 'Projetor, Quadro, Mesas, Cadeiras, Computadores',
            'Quadro', 'Projetor, Quadro, Mesas, Cadeiras', 'Mesas, Cadeiras', 'Mesas, Cadeiras, Computadores'
        ]
    }
    st.session_state.df_salas = pd.DataFrame(data_padrao)

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
            coluna_atual = [c1, c2, c3][i % 3]
            with coluna_atual:
                if st.checkbox(opcao, key=f"add_{opcao}"):
                    recursos_selecionados.append(opcao)
        
        st.markdown("---")
        col_submit, col_cancel = st.columns(2)
        submit = col_submit.form_submit_button("💾 Salvar Sala", type="primary")
        
        if submit:
            if cod and desc: 
                rec_str = ", ".join(recursos_selecionados)
                nova_linha = {
                    'Código': cod, 'Descrição': desc, 'Ambiente': amb, 
                    'Capacidade': cap, 'Recursos': rec_str
                }
                st.session_state.df_salas = pd.concat(
                    [st.session_state.df_salas, pd.DataFrame([nova_linha])], 
                    ignore_index=True
                )
                st.rerun()
            else:
                st.error("Preencha pelo menos o Código e a Descrição.")

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
    recursos_atuais_str = str(sala_atual['Recursos'])
    recursos_atuais_lista = [r.strip() for r in recursos_atuais_str.split(',')]
    
    c1, c2, c3 = st.columns(3)
    novos_recursos_selecionados = []
    
    for i, opcao in enumerate(OPCOES_RECURSOS):
        coluna_atual = [c1, c2, c3][i % 3]
        with coluna_atual:
            esta_marcado = opcao in recursos_atuais_lista
            if st.checkbox(opcao, value=esta_marcado, key=f"edit_{opcao}"):
                novos_recursos_selecionados.append(opcao)

    st.markdown("---")
    col_salvar, col_cancelar = st.columns([1, 1])
    
    if col_salvar.button("💾 Salvar Alterações", type="primary", use_container_width=True):
        novo_rec_str = ", ".join(novos_recursos_selecionados)
        
        st.session_state.df_salas.at[index_selecionado, 'Código'] = novo_cod
        st.session_state.df_salas.at[index_selecionado, 'Descrição'] = nova_desc
        st.session_state.df_salas.at[index_selecionado, 'Ambiente'] = novo_amb
        st.session_state.df_salas.at[index_selecionado, 'Capacidade'] = novo_cap
        st.session_state.df_salas.at[index_selecionado, 'Recursos'] = novo_rec_str
        st.rerun()

    if col_cancelar.button("❌ Cancelar", type="secondary", use_container_width=True):
        st.rerun() 

@st.dialog("🗑️ Confirmar Exclusão")
def modal_excluir_sala(index_selecionado):
    sala_atual = st.session_state.df_salas.iloc[index_selecionado]
    
    st.warning("⚠️ Tem certeza que deseja excluir esta sala permanentemente?")
    st.write(f"**Sala:** {sala_atual['Código']} - {sala_atual['Descrição']}")
    
    col_sim, col_nao = st.columns(2)
    
    if col_sim.button("Sim, Excluir", type="primary", use_container_width=True):
        st.session_state.df_salas = st.session_state.df_salas.drop(index_selecionado).reset_index(drop=True)
        st.rerun() 
        
    if col_nao.button("Cancelar", type="secondary", use_container_width=True):
        st.rerun() 

# --- LÓGICA DE NEGÓCIO (ALOCAÇÃO) ---
def verificar_conflito_horario(t1_inicio, t1_fim, t2_inicio, t2_fim):
    return max(t1_inicio, t2_inicio) < min(t1_fim, t2_fim)

def alocar_salas(df_turmas, df_salas):
    alocacoes = []
    ocupacao_salas = {codigo: [] for codigo in df_salas['Código'].unique()}
    
    for index, row in df_turmas.iterrows():
        # --- LÓGICA DE MÚLTIPLOS DIAS ---
        # 1. Lê a coluna Dia
        raw_dias = str(row['Dia'])
        
        # 2. Normaliza separadores (troca / e " e " por vírgula)
        raw_dias = raw_dias.replace('/', ',').replace(' e ', ',').replace(' E ', ',')
        
        # 3. Cria lista de dias limpa (remove espaços em branco)
        lista_dias = [d.strip() for d in raw_dias.split(',')]

        # 4. Itera para CADA dia encontrado na célula
        for dia_atual in lista_dias:
            if not dia_atual: continue # Pula se estiver vazio
            
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
                        # Verifica conflito APENAS no dia atual do loop
                        if agendamento['dia'] == dia_atual:
                            if verificar_conflito_horario(inicio, fim, agendamento['inicio'], agendamento['fim']):
                                conflito = True
                                break
                
                if not conflito:
                    ocupacao_salas[codigo_sala].append({'dia': dia_atual, 'inicio': inicio, 'fim': fim})
                    alocacoes.append({
                        'Cód. Matéria': row['Codigo'],
                        'Disciplina': row['Nome'],
                        'Professor': row['Professor'],
                        'Qtd_Alunos': qtd_alunos,
                        'Sala Alocada': f"{sala['Código']} - {sala['Ambiente']}",
                        'Capacidade': sala['Capacidade'],
                        'Ocupação': f"{(qtd_alunos/sala['Capacidade'])*100:.0f}%",
                        'Dia': dia_atual, # Mostra o dia específico
                        'Horário': f"{row['Inicio']} - {row['Fim']}",
                        'Status': 'Sucesso'
                    })
                    turma_alocada = True
                    break 
            
            if not turma_alocada:
                alocacoes.append({
                    'Cód. Matéria': row['Codigo'],
                    'Disciplina': row['Nome'],
                    'Professor': row['Professor'],
                    'Qtd_Alunos': qtd_alunos,
                    'Sala Alocada': 'NÃO ALOCADA',
                    'Capacidade': '-',
                    'Ocupação': '-',
                    'Dia': dia_atual,
                    'Horário': f"{row['Inicio']} - {row['Fim']}",
                    'Status': 'Erro: Sem sala compatível'
                })

    return pd.DataFrame(alocacoes)

# --- LAYOUT PRINCIPAL ---

col1, col2 = st.columns([1.2, 1.5], gap="large")

with col1:
    st.subheader("1. Gerenciar Salas")
    
    with st.expander("📂 Importar/Exportar Excel de Salas"):
        st.info("Baixe a planilha atual, edite no Excel e suba novamente para atualizar as salas.")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state.df_salas.to_excel(writer, index=False)
        
        st.download_button(
            label="⬇️ Baixar Modelo Atual (com salas cadastradas)",
            data=buffer.getvalue(),
            file_name="modelo_salas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        
        upload_salas_update = st.file_uploader("Subir Planilha Atualizada", type=['xlsx'], key="upload_salas_update")
        
        if upload_salas_update:
            try:
                df_novo = pd.read_excel(upload_salas_update)
                colunas_esperadas = ['Código', 'Descrição', 'Ambiente', 'Capacidade', 'Recursos']
                if all(col in df_novo.columns for col in colunas_esperadas):
                    if st.button("Confirmar Atualização de Salas", type="primary"):
                        st.session_state.df_salas = df_novo
                        st.success("Salas atualizadas com sucesso!")
                        st.rerun()
                else:
                    st.error(f"A planilha precisa ter as colunas: {', '.join(colunas_esperadas)}")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")

    event = st.dataframe(
        st.session_state.df_salas,
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True,
        hide_index=True
    )

    linhas_selecionadas = event.selection.rows
    
    if st.button("➕ Adicionar Sala", use_container_width=True):
        modal_adicionar_sala()

    st.write("") 

    col_btn_edit, col_btn_del = st.columns(2)
    
    if linhas_selecionadas:
        index_selecionado = linhas_selecionadas[0]
        
        if col_btn_edit.button("✏️ Editar", use_container_width=True):
            modal_editar_sala(index_selecionado)
            
        if col_btn_del.button("🗑️ Excluir", type="primary", use_container_width=True):
            modal_excluir_sala(index_selecionado)
    else:
        col_btn_edit.button("✏️ Editar", disabled=True, use_container_width=True, help="Selecione uma sala na tabela acima")
        col_btn_del.button("🗑️ Excluir", disabled=True, use_container_width=True, help="Selecione uma sala na tabela acima")

with col2:
    st.subheader("2. Upload de Turmas")
    
    with st.expander("📝 Baixar Modelo de Planilha de Turmas"):
        st.markdown("""
        Baixe este modelo para preencher suas turmas corretamente.\n
        **Respeite os cabeçalhos e lembre-se de apagar as linhas de exemplo.**\n
        Dica: **Você pode colocar múltiplos dias na mesma linha separando por vírgula.**
        Ex: `Segunda, Quarta` ou `Terça / Quinta`.
        """)
        
        df_modelo_turmas = pd.DataFrame({
            'Codigo': ['MAT-101', 'MEC-202', 'FIS-303'],
            'Nome': ['Cálculo I', 'Termodinâmica', 'Física Experimental'],
            'Professor': ['João Silva', 'Maria Santos', 'Pedro Souza'],
            'Qtd_Alunos': [45, 20, 15],
            'Inicio': ['08:00', '10:00', '14:00'],
            'Fim': ['10:00', '12:00', '16:00'],
            'Dia': ['Segunda, Quarta', 'Terça', 'Sexta'],
            'Necessidades': ['Projetor', 'Laboratório', '']
        })
        
        buffer_turmas = io.BytesIO()
        with pd.ExcelWriter(buffer_turmas, engine='openpyxl') as writer:
            df_modelo_turmas.to_excel(writer, index=False)
            
        st.download_button(
            label="⬇️ Baixar Modelo de Turmas (.xlsx)",
            data=buffer_turmas.getvalue(),
            file_name="modelo_importacao_turmas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    upload_arquivo = st.file_uploader("Subir arquivo Excel das Matérias", type=['xlsx'])

    if upload_arquivo is not None:
        try:
            df_turmas = pd.read_excel(upload_arquivo)
            
            st.write("Prévia das Turmas Carregadas:")
            st.dataframe(df_turmas.head(3), hide_index=True)
            
            if st.button("🚀 Processar Alocação", type="primary"):
                colunas_necessarias = ['Codigo', 'Nome', 'Professor', 'Qtd_Alunos', 'Inicio', 'Fim', 'Dia']
                
                if all(col in df_turmas.columns for col in colunas_necessarias):
                    with st.spinner('Calculando melhor distribuição...'):
                        resultado = alocar_salas(df_turmas, st.session_state.df_salas)
                    
                    st.divider()
                    st.subheader("3. Resultados da Alocação")
                    
                    if not resultado.empty:
                        sucesso = len(resultado[resultado['Status'] == 'Sucesso'])
                        total = len(resultado)
                        st.progress(sucesso/total if total > 0 else 0)
                        st.caption(f"Sucesso: {sucesso} de {total} alocações realizadas (cada dia conta como uma alocação).")

                        def color_status(val):
                            color = '#d4edda' if val == 'Sucesso' else '#f8d7da'
                            return f'background-color: {color}'

                        st.dataframe(
                            resultado.style.applymap(color_status, subset=['Status']),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.warning("Nenhuma alocação gerada. Verifique se o arquivo não está vazio.")
                else:
                    st.error(f"Erro: O arquivo Excel precisa ter as colunas exatas: {', '.join(colunas_necessarias)}")
                    st.warning("Dica: Baixe o modelo acima para garantir o formato correto.")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")