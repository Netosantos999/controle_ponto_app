import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- Configurações do Aplicativo ---
st.set_page_config(
    page_title="Controle de Ponto",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:suporte@suaempresa.com',
        'Report a bug': 'mailto:suporte@suaempresa.com',
        'About': '''
            ## Controle de Ponto
            Sistema para registro e gerenciamento de ponto dos colaboradores.
        '''
    }
)

# --- Constantes e Funções de Dados ---
ARQ_PONTO = "registro_ponto.csv"
ARQ_COLAB = "colaboradores.csv"

def inicializar_arquivos():
    if not os.path.exists(ARQ_COLAB):
        pd.DataFrame(columns=["Nome", "Funcao"]).to_csv(ARQ_COLAB, index=False)
    if not os.path.exists(ARQ_PONTO):
        pd.DataFrame(columns=["Nome", "Ação", "Data", "Hora"]).to_csv(ARQ_PONTO, index=False)

def carregar_colaboradores():
    try:
        return pd.read_csv(ARQ_COLAB)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["Nome", "Funcao"])

def salvar_colaboradores(df):
    df.to_csv(ARQ_COLAB, index=False)

def adicionar_colaborador(nome, funcao):
    df = carregar_colaboradores()
    if nome and nome not in df["Nome"].values:
        novo_colaborador = pd.DataFrame([[nome, funcao]], columns=["Nome", "Funcao"])
        df = pd.concat([df, novo_colaborador], ignore_index=True)
        salvar_colaboradores(df)
        return True
    return False

def remover_colaborador(nome):
    df = carregar_colaboradores()
    initial_len = len(df)
    df = df[df["Nome"] != nome]
    salvar_colaboradores(df)
    return len(df) < initial_len

def editar_colaborador(nome_original, novo_nome, nova_funcao):
    df = carregar_colaboradores()
    if nome_original in df["Nome"].values:
        if novo_nome and novo_nome != nome_original and novo_nome in df["Nome"].values:
            return False
        
        idx = df[df["Nome"] == nome_original].index[0]
        df.loc[idx, "Nome"] = novo_nome
        df.loc[idx, "Funcao"] = nova_funcao
        salvar_colaboradores(df)

        if novo_nome and novo_nome != nome_original:
            df_pontos = carregar_pontos()
            df_pontos.loc[df_pontos["Nome"] == nome_original, "Nome"] = novo_nome
            df_pontos.to_csv(ARQ_PONTO, index=False)
            
        return True
    return False

def carregar_pontos():
    try:
        return pd.read_csv(ARQ_PONTO)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["Nome", "Ação", "Data", "Hora"])

def registrar_evento(nome, acao, data_str=None, hora_str=None):
    if data_str is None:
        data_str = datetime.now().strftime("%Y-%m-%d")
    if hora_str is None:
        hora_str = datetime.now().strftime("%H:%M")
        
    novo_registro = pd.DataFrame([[nome, acao, data_str, hora_str]], columns=["Nome", "Ação", "Data", "Hora"])
    df_pontos = carregar_pontos()
    df_pontos = pd.concat([df_pontos, novo_registro], ignore_index=True)
    df_pontos.to_csv(ARQ_PONTO, index=False)

def registrar_saida_com_almoco(nome):
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    registrar_evento(nome, "Pausa", data_str=data_hoje, hora_str="12:00")
    registrar_evento(nome, "Retorno", data_str=data_hoje, hora_str="13:00")
    registrar_evento(nome, "Saída")
    return datetime.now().strftime("%H:%M")

def atualizar_ponto(index_para_atualizar, nome, acao, data, hora):
    df = carregar_pontos()
    if 0 <= index_para_atualizar < len(df):
        df.loc[index_para_atualizar, "Nome"] = nome
        df.loc[index_para_atualizar, "Ação"] = acao
        df.loc[index_para_atualizar, "Data"] = data
        df.loc[index_para_atualizar, "Hora"] = hora
        df.to_csv(ARQ_PONTO, index=False)
        return True
    return False

def deletar_ponto(index_para_deletar):
    df = carregar_pontos()
    if 0 <= index_para_deletar < len(df):
        df = df.drop(index_para_deletar).reset_index(drop=True)
        df.to_csv(ARQ_PONTO, index=False)
        return True
    return False

def calcular_horas(df):
    resultado = []
    for nome in df["Nome"].unique():
        for data_str in df[df["Nome"] == nome]["Data"].unique():
            df_dia_nome = df[(df["Nome"] == nome) & (df["Data"] == data_str)].sort_values(by="Hora")
            
            tempo_trabalhado = timedelta(0)
            ultimo_evento_entrada = None

            for _, row in df_dia_nome.iterrows():
                # --- LINHA CORRIGIDA ---
                # Garante que a string de hora esteja sempre no formato HH:MM
                hora_str_processada = str(row["Hora"])
                if hora_str_processada.count(':') == 2:
                    # Se a hora tiver segundos (ex: "08:30:00"), remove-os
                    hora_str_processada = ":".join(hora_str_processada.split(':')[:2])
                
                hora_evento = datetime.strptime(hora_str_processada, "%H:%M")
                # --- FIM DA CORREÇÃO ---
                
                if row["Ação"] in ["Entrada", "Retorno"]:
                    ultimo_evento_entrada = hora_evento
                elif row["Ação"] in ["Pausa", "Saída"] and ultimo_evento_entrada:
                    periodo = hora_evento - ultimo_evento_entrada
                    tempo_trabalhado += periodo
                    ultimo_evento_entrada = None

            if tempo_trabalhado > timedelta(0):
                total_seconds = int(tempo_trabalhado.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                formatted_time = f"{int(hours):02}:{int(minutes):02}"
                resultado.append((nome, data_str, formatted_time))
            else:
                if not df_dia_nome.empty:
                    resultado.append((nome, data_str, "Registro Incompleto"))

    return pd.DataFrame(resultado, columns=["Nome", "Data", "Horas Trabalhadas"])

# --- Inicialização ---
inicializar_arquivos()

# --- Interface Principal ---
st.title("Controle de Ponto")
st.markdown("Sistema para registro e gerenciamento de ponto dos colaboradores.")

aba = st.sidebar.radio("Navegação", ["Registrar Ponto", "Gerenciar Colaboradores", "Relatórios", "Ajustar Ponto"])

#inicio da mudança para que o usuario possa escolher a hora e data ou não

if aba == "Registrar Ponto":
    st.header("Registro de Ponto")
    st.markdown("Informe manualmente a data e hora da entrada. O sistema registrará automaticamente:")
    st.markdown("- Pausa às 12:00")
    st.markdown("- Retorno às 13:00")
    st.markdown("- Saída às 17:00 (segunda a quinta) ou 16:00 (sexta)")

    df_colab = carregar_colaboradores()
    nomes = [""] + df_colab["Nome"].tolist()

    with st.container(border=True):
        nome_selecionado = st.selectbox(
            "**Selecione seu nome:**",
            nomes,
            key="ponto_nome_select",
            help="Escolha seu nome para registrar o ponto."
        )

        if nome_selecionado:
            st.write(f"Colaborador selecionado: **{nome_selecionado}**")

            data_input = st.date_input("Data do Registro:", datetime.today(), key="data_input_manual")
            hora_input = st.text_input("Hora da Entrada (HH:MM):", placeholder="Ex: 08:00", key="hora_input_manual")

            col1, col2 = st.columns(2)

            try:
                datetime.strptime(hora_input, "%H:%M")  # Valida formato
                data_str = data_input.strftime("%Y-%m-%d")
                hora_str = hora_input.strip()

                if col1.button("Registrar Entrada", use_container_width=True):
                    registrar_evento(nome_selecionado, "Entrada", data_str, hora_str)
                    registrar_evento(nome_selecionado, "Pausa", data_str, "12:00")
                    registrar_evento(nome_selecionado, "Retorno", data_str, "13:00")

                    dia_semana = datetime.strptime(data_str, "%Y-%m-%d").weekday()
                    hora_saida = "16:00" if dia_semana == 4 else "17:00"

                    registrar_evento(nome_selecionado, "Saída", data_str, hora_saida)

                    st.success(
                        f"Entrada registrada às {hora_str}, pausa às 12:00, retorno às 13:00 "
                        f"e saída às {hora_saida} em {data_str}."
                    )

                
            except ValueError:
                st.error("Use o formato HH:MM.")
        else:
            st.warning("Por favor, selecione um nome.")



#fim da mudança para que o usuario possa escolher a hora e data ou não

elif aba == "Gerenciar Colaboradores":
    st.header("Gerenciamento de Colaboradores")
    st.markdown("Adicione, edite ou remova colaboradores do sistema.")

    with st.expander("Adicionar Novo Colaborador", expanded=True):
        st.markdown("Preencha os campos abaixo para adicionar um novo colaborador.")
        with st.form("form_add_colaborador", clear_on_submit=True):
            nome_novo = st.text_input("Nome completo", placeholder="Ex: João da Silva").strip()
            funcao_novo = st.text_input("Função", placeholder="Ex: Pedreiro").strip()
            submitted_add = st.form_submit_button("Adicionar Colaborador")

            if submitted_add:
                if nome_novo and funcao_novo:
                    if adicionar_colaborador(nome_novo, funcao_novo):
                        st.success(f"O colaborador **{nome_novo}** ({funcao_novo}) foi adicionado com sucesso.")
                    else:
                        st.warning(f"O colaborador '{nome_novo}' já existe. Por favor, utilize um nome diferente.")
                else:
                    st.error("Por favor, preencha o nome e a função do colaborador.")
    
    with st.expander("Editar Colaborador"):
        st.markdown("Selecione um colaborador para atualizar suas informações.")
        df_colab = carregar_colaboradores()
        nomes_existentes = [""] + df_colab["Nome"].tolist()
        
        colab_para_editar = st.selectbox("**Selecione o colaborador para editar:**", nomes_existentes, key="edit_select_box_main")
        
        if colab_para_editar:
            with st.form("form_edit_colaborador"):
                current_info = df_colab[df_colab["Nome"] == colab_para_editar].iloc[0]
                novo_nome_edit = st.text_input("Novo nome completo", value=current_info["Nome"]).strip()
                nova_funcao_edit = st.text_input("Nova função", value=current_info["Funcao"]).strip()
                submitted_edit = st.form_submit_button("Salvar Alterações")

                if submitted_edit:
                    if editar_colaborador(colab_para_editar, novo_nome_edit, nova_funcao_edit):
                        st.success(f"Os dados do colaborador **{colab_para_editar}** foram atualizados com sucesso.")
                        st.rerun()
                    else:
                        st.error(f"Não foi possível atualizar: o nome '{novo_nome_edit}' já está em uso.")
    
    with st.expander("Remover Colaborador"):
        st.markdown("Atenção: esta ação não pode ser desfeita.")
        df_colab_atual = carregar_colaboradores()
        nomes_para_remover = [""] + df_colab_atual["Nome"].tolist()
        
        with st.form("form_remove_colaborador"):
            nome_remover = st.selectbox("**Selecione o nome para remover:**", nomes_para_remover, key="remove_select_box_form")
            confirmar = st.checkbox("Confirmo que desejo remover este colaborador permanentemente.")
            submitted_remove = st.form_submit_button("Remover Colaborador")

            if submitted_remove:
                if nome_remover and confirmar:
                    if remover_colaborador(nome_remover):
                        st.warning(f"O colaborador **{nome_remover}** foi removido do sistema.")
                        st.rerun()
                    else:
                        st.error("Ocorreu um erro ao remover o colaborador.")
                elif not nome_remover:
                    st.warning("Por favor, selecione um colaborador.")
                else:
                    st.info("É necessário marcar a caixa de confirmação para remover.")

    st.markdown("---")
    st.subheader("Lista de Colaboradores")
    df_colab_final = carregar_colaboradores()
    if not df_colab_final.empty:
        st.dataframe(df_colab_final, use_container_width=True)
    else:
        st.info("Nenhum colaborador cadastrado no sistema.")

elif aba == "Relatórios":
    st.header("Relatórios de Ponto")
    st.markdown("Visualize o histórico de ponto e o resumo de horas trabalhadas por data.")

    st.subheader("Histórico Detalhado por Data")
    col_date, col_name_report = st.columns([1, 2])
    with col_date:
        data_relatorio = st.date_input("Selecione uma data:", datetime.today(), key="rel_date_input")
    with col_name_report:
        df_colab_report = carregar_colaboradores()
        nomes_relatorio = ["Todos"] + df_colab_report["Nome"].tolist()
        colab_relatorio = st.selectbox("Filtrar por Colaborador:", nomes_relatorio, key="rel_colab_select")

    df_pontos_full = carregar_pontos()
    
    df_dia = df_pontos_full[df_pontos_full["Data"] == data_relatorio.strftime("%Y-%m-%d")]
    
    if colab_relatorio != "Todos":
        df_dia = df_dia[df_dia["Nome"] == colab_relatorio]

    st.write(f"**Registros de Ponto para {data_relatorio.strftime('%d/%m/%Y')}:**")
    if not df_dia.empty:
        st.dataframe(df_dia.sort_values(by=["Nome", "Hora"]), use_container_width=True)
    else:
        st.info("Nenhum registro encontrado para a data e filtro selecionados.")



    st.markdown("---")
    st.subheader("Cálculo de Horas Trabalhadas")
    st.markdown("As horas são calculadas somando os períodos (Entrada-Pausa) e (Retorno-Saída).")
    
    df_horas = calcular_horas(df_pontos_full[df_pontos_full["Data"] == data_relatorio.strftime("%Y-%m-%d")])
    
    if colab_relatorio != "Todos":
        df_horas = df_horas[df_horas["Nome"] == colab_relatorio]

    if not df_horas.empty:
        st.dataframe(df_horas, use_container_width=True)
    else:
        st.info("Nenhum cálculo de horas disponível para a data e filtro selecionados.")

elif aba == "Ajustar Ponto":
    st.header("Ajuste Manual de Ponto")
    st.markdown("Esta ferramenta permite a correção e o ajuste manual dos registros de ponto.")
    
    df_colab_ajuste = carregar_colaboradores()
    nomes_ajuste = [""] + df_colab_ajuste["Nome"].tolist()
    
    col_ajuste_sel, col_ajuste_date = st.columns(2)
    with col_ajuste_sel:
        colab_selecionado = st.selectbox("**Selecione o Colaborador:**", nomes_ajuste, key="ajustar_colab_select_main")
    with col_ajuste_date:
        data_ajuste = st.date_input("**Selecione a Data do Ajuste:**", datetime.today(), key="ajustar_date_input_main")
    
    if colab_selecionado:
        df_pontos = carregar_pontos()
        registros_do_dia = df_pontos[
            (df_pontos["Nome"] == colab_selecionado) & 
            (df_pontos["Data"] == data_ajuste.strftime("%Y-%m-%d"))
        ].sort_values(by="Hora").reset_index()
        
        st.markdown(f"#### Registros para **{colab_selecionado}** em **{data_ajuste.strftime('%d/%m/%Y')}**")
        
        if not registros_do_dia.empty:
            for i, row in registros_do_dia.iterrows():
                original_index = row['index']
                
                with st.container(border=True):
                    st.markdown(f"**Registro ID `{original_index}`:**")
                    col_acao, col_data, col_hora = st.columns(3)
                    
                    novo_acao = col_acao.selectbox("Ação", ["Entrada", "Pausa", "Retorno", "Saída"], index=["Entrada", "Pausa", "Retorno", "Saída"].index(row["Ação"]), key=f"ajust_acao_{original_index}")
                    novo_data_str = col_data.text_input("Data (YYYY-MM-DD)", value=row["Data"], key=f"ajust_data_{original_index}").strip()
                    novo_hora_str = col_hora.text_input("Hora (HH:MM)", value=row["Hora"], key=f"ajust_hora_{original_index}").strip()
                    
                    col_update, col_delete = st.columns(2)
                    if col_update.button("Salvar Alterações", use_container_width=True, key=f"update_btn_{original_index}"):
                        try:
                            datetime.strptime(novo_data_str, "%Y-%m-%d")
                            datetime.strptime(novo_hora_str, "%H:%M")
                            
                            if atualizar_ponto(original_index, colab_selecionado, novo_acao, novo_data_str, novo_hora_str):
                                st.success(f"O registro ID {original_index} foi atualizado com sucesso.")
                                st.rerun()
                        except ValueError:
                            st.error("Formato de Data (YYYY-MM-DD) ou Hora (HH:MM) inválido.")
                    
                    if col_delete.button("Excluir Registro", use_container_width=True, key=f"delete_btn_{original_index}"):
                        if deletar_ponto(original_index):
                            st.warning(f"O registro ID {original_index} foi excluído.")
                            st.rerun()

        st.markdown("### Adicionar Novo Registro Manual")
        with st.form("form_add_ponto_manual"):
            col_add_acao, col_add_data, col_add_hora = st.columns(3)
            acao_manual = col_add_acao.selectbox("Ação", ["Entrada", "Pausa", "Retorno", "Saída"], key="add_manual_acao")
            data_manual_str = col_add_data.text_input("Data (YYYY-MM-DD)", value=data_ajuste.strftime("%Y-%m-%d")).strip()
            hora_manual_str = col_add_hora.text_input("Hora (HH:MM)", value=datetime.now().strftime("%H:%M")).strip()
            
            if st.form_submit_button("Adicionar Registro"):
                try:
                    datetime.strptime(data_manual_str, "%Y-%m-%d")
                    datetime.strptime(hora_manual_str, "%H:%M")
                    registrar_evento(colab_selecionado, acao_manual, data_manual_str, hora_manual_str)
                    st.success("Novo registro manual adicionado com sucesso.")
                    st.rerun()
                except ValueError:
                    st.error("Formato de Data (YYYY-MM-DD) ou Hora (HH:MM) inválido.")
    else:
        st.info("Selecione um colaborador e uma data para visualizar e ajustar os registros.")

# aquii

st.markdown("---")
st.subheader("📥 Baixar Arquivos CSV")

df_csv_registros = carregar_pontos()
df_csv_colaboradores = carregar_colaboradores()

st.download_button(
    label="⬇️ Baixar Registros de Ponto (registro_ponto.csv)",
    data=df_csv_registros.to_csv(index=False).encode('utf-8'),
    file_name='registro_ponto.csv',
    mime='text/csv'
)

st.download_button(
    label="⬇️ Baixar Lista de Colaboradores (colaboradores.csv)",
    data=df_csv_colaboradores.to_csv(index=False).encode('utf-8'),
    file_name='colaboradores.csv',
    mime='text/csv'
)

