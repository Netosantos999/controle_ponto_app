import streamlit as st
import pandas as pd
from datetime import datetime, timedelta # Import timedelta for easier time calculations
import os

# --- Configurações do Aplicativo ---
st.set_page_config(
    page_title="Controle de Ponto Inteligente",
    layout="centered", # ou "wide" para ocupar toda a largura
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:seu.email@example.com',
        'Report a bug': 'mailto:seu.email@example.com',
        'About': '''
            ## Controle de Ponto Inteligente
            Um aplicativo simples para gerenciar registros de ponto de colaboradores.
            Desenvolvido com Streamlit.
        '''
    }
)

# --- Constantes e Funções de Dados ---
ARQ_PONTO = "registro_ponto.csv"
ARQ_COLAB = "colaboradores.csv"

def inicializar_colaboradores():
    if not os.path.exists(ARQ_COLAB):
        pd.DataFrame(columns=["Nome", "Funcao"]).to_csv(ARQ_COLAB, index=False)

def carregar_colaboradores():
    inicializar_colaboradores()
    try:
        return pd.read_csv(ARQ_COLAB)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["Nome", "Funcao"])


def salvar_colaboradores(df):
    df.to_csv(ARQ_COLAB, index=False)

def adicionar_colaborador(nome, funcao):
    df = carregar_colaboradores()
    if nome and nome not in df["Nome"].values:
        df.loc[len(df)] = [nome, funcao]
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
        # Check if the new name already exists and it's not the original name
        if novo_nome and novo_nome != nome_original and novo_nome in df["Nome"].values:
            return False # New name already exists
        
        idx = df[df["Nome"] == nome_original].index[0]
        if novo_nome:
            df.loc[idx, "Nome"] = novo_nome
        if nova_funcao:
            df.loc[idx, "Funcao"] = nova_funcao
        salvar_colaboradores(df)

        # Also update the name in registro_ponto.csv if the name changed
        if novo_nome and novo_nome != nome_original:
            df_pontos = carregar_pontos()
            df_pontos.loc[df_pontos["Nome"] == nome_original, "Nome"] = novo_nome
            df_pontos.to_csv(ARQ_PONTO, index=False)
            
        return True
    return False

def carregar_pontos():
    if os.path.exists(ARQ_PONTO):
        try:
            return pd.read_csv(ARQ_PONTO)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=["Nome", "Ação", "Data", "Hora"])
    return pd.DataFrame(columns=["Nome", "Ação", "Data", "Hora"])

def salvar_ponto(nome, acao):
    agora = datetime.now()
    data = agora.strftime("%Y-%m-%d")
    hora = agora.strftime("%H:%M:%S")
    novo = pd.DataFrame([[nome, acao, data, hora]], columns=["Nome", "Ação", "Data", "Hora"])
    df = carregar_pontos()
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(ARQ_PONTO, index=False)

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
        df_nome = df[df["Nome"] == nome].sort_values(by=["Data", "Hora"]) # Sort by Date and then Hora
        
        # Group entries by date for each person
        for date_str in df_nome["Data"].unique():
            df_dia_nome = df_nome[df_nome["Data"] == date_str].sort_values(by="Hora")
            
            entradas = df_dia_nome[df_dia_nome["Ação"] == "Entrada"]
            saidas = df_dia_nome[df_dia_nome["Ação"] == "Saída"]

            tempo_trabalhado = timedelta(0) # Initialize as zero timedelta
            
            # Simple approach: sum up periods between (Entry, Exit) or (Return, Pause/Exit)
            # This is a simplification and might need more complex logic for complex cases (multiple pauses)
            
            # For simplicity, let's assume one entry/exit pair per day for total work duration
            if not entradas.empty and not saidas.empty:
                primeira_entrada = datetime.strptime(entradas.iloc[0]["Hora"], "%H:%M:%S")
                ultima_saida = datetime.strptime(saidas.iloc[-1]["Hora"], "%H:%M:%S")
                tempo_trabalhado = ultima_saida - primeira_entrada
            
            # Format timedelta to HH:MM:SS or HH:MM
            total_seconds = int(tempo_trabalhado.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            
            if tempo_trabalhado > timedelta(0): # If there was a positive work duration
                resultado.append((nome, date_str, formatted_time))
            else:
                resultado.append((nome, date_str, "Incompleto / Sem Saída Válida"))
    
    return pd.DataFrame(resultado, columns=["Nome", "Data", "Horas Trabalhadas"])


# --- Interface Principal ---
st.title("⏰ Controle de Ponto Inteligente")
st.markdown("Seja bem-vindo(a) ao sistema de gestão de ponto.")

aba = st.sidebar.radio("📌 Navegação", ["Registrar Ponto", "Gerenciar Colaboradores", "Relatórios", "Ajustar Ponto"])

if aba == "Registrar Ponto":
    st.header("✅ Registro de Ponto")
    st.markdown("Selecione seu nome e clique na ação correspondente.")

    df_colab = carregar_colaboradores()
    nomes = [""] + df_colab["Nome"].tolist()
    
    with st.container(border=True):
        nome_selecionado = st.selectbox(
            "👤 **Selecione seu nome:**",
            nomes,
            key="ponto_nome_select",
            help="Escolha seu nome para registrar uma ação."
        )

        if nome_selecionado:
            st.write(f"Olá, **{nome_selecionado}**!")
            col1, col2, col3, col4 = st.columns(4)
            
            if col1.button("✅ Entrada", use_container_width=True):
                salvar_ponto(nome_selecionado, "Entrada")
                st.success(f"✔️ Entrada registrada para **{nome_selecionado}** às {datetime.now().strftime('%H:%M:%S')}")
            if col2.button("⏸️ Pausa", use_container_width=True):
                salvar_ponto(nome_selecionado, "Pausa")
                st.info(f"⏸️ Pausa registrada para **{nome_selecionado}** às {datetime.now().strftime('%H:%M:%S')}")
            if col3.button("▶️ Retorno", use_container_width=True):
                salvar_ponto(nome_selecionado, "Retorno")
                st.info(f"▶️ Retorno registrado para **{nome_selecionado}** às {datetime.now().strftime('%H:%M:%S')}")
            if col4.button("🏁 Saída", use_container_width=True):
                salvar_ponto(nome_selecionado, "Saída")
                st.success(f"🏁 Saída registrada para **{nome_selecionado}** às {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("⚠️ Por favor, selecione seu nome para registrar o ponto.")

elif aba == "Gerenciar Colaboradores":
    st.header("👥 Gerenciamento de Colaboradores")
    st.markdown("Adicione, edite ou remova colaboradores do sistema.")

    # --- Adicionar Colaborador ---
    with st.expander("➕ Adicionar Novo Colaborador", expanded=True):
        st.markdown("Preencha os campos abaixo para adicionar um novo membro à equipe.")
        with st.form("form_add_colaborador", clear_on_submit=True):
            nome_novo = st.text_input("Nome completo", placeholder="Ex: Maria Silva", key="add_nome_input").strip()
            funcao_novo = st.text_input("Função (ex: Pedreiro, Ajudante)", placeholder="Ex: Pedreiro", key="add_funcao_input").strip()
            submitted_add = st.form_submit_button("Adicionar Colaborador 🚀")

            if submitted_add:
                if nome_novo and funcao_novo:
                    if adicionar_colaborador(nome_novo, funcao_novo):
                        st.success(f"🎉 **{nome_novo}** ({funcao_novo}) adicionado com sucesso!")
                        # Streamlit automatically clears form inputs if clear_on_submit is True
                    else:
                        st.warning(f"⚠️ Colaborador '**{nome_novo}**' já existe. Tente um nome diferente.")
                else:
                    st.error("❌ Por favor, preencha o nome e a função do colaborador.")
    
    # --- Editar Colaborador ---
    with st.expander("✏️ Editar Informações do Colaborador"):
        st.markdown("Selecione um colaborador e atualize seu nome ou função.")
        df_colab = carregar_colaboradores()
        nomes_existentes = [""] + df_colab["Nome"].tolist()
        
        # Persist selected name for editing across reruns
        if 'edit_selected_name' not in st.session_state:
            st.session_state.edit_selected_name = ""
        if 'edit_new_name_val' not in st.session_state:
            st.session_state.edit_new_name_val = ""
        if 'edit_new_funcao_val' not in st.session_state:
            st.session_state.edit_new_funcao_val = ""

        colab_para_editar = st.selectbox(
            "👤 **Selecione o colaborador para editar:**",
            nomes_existentes,
            key="edit_select_box_main"
        )
        
        if colab_para_editar and st.session_state.edit_selected_name != colab_para_editar:
            # If a new collaborator is selected, update the text input values
            selected_colab_info = df_colab[df_colab["Nome"] == colab_para_editar].iloc[0]
            st.session_state.edit_new_name_val = selected_colab_info["Nome"]
            st.session_state.edit_new_funcao_val = selected_colab_info["Funcao"]
            st.session_state.edit_selected_name = colab_para_editar
            st.rerun() # Rerun to update input fields with current values

        with st.form("form_edit_colaborador"):
            # Use session state values for default text input values
            novo_nome_edit = st.text_input(
                "📝 Novo nome completo (deixe em branco para não alterar)", 
                value=st.session_state.edit_new_name_val, 
                key="edit_new_name_input_form"
            ).strip()
            nova_funcao_edit = st.text_input(
                "💼 Nova função (deixe em branco para não alterar)", 
                value=st.session_state.edit_new_funcao_val, 
                key="edit_new_funcao_input_form"
            ).strip()
            submitted_edit = st.form_submit_button("Salvar Edições ✨")

            if submitted_edit:
                if colab_para_editar:
                    # Determine effective new_name and new_funcao
                    current_colab_info = df_colab[df_colab["Nome"] == colab_para_editar].iloc[0]
                    effective_new_name = novo_nome_edit if novo_nome_edit else current_colab_info["Nome"]
                    effective_new_funcao = nova_funcao_edit if nova_funcao_edit else current_colab_info["Funcao"]

                    if not novo_nome_edit and not nova_funcao_edit:
                        st.warning("⚠️ Por favor, preencha o novo nome ou a nova função para editar.")
                    elif editar_colaborador(colab_para_editar, effective_new_name, effective_new_funcao):
                        st.success(f"✅ Dados de **{colab_para_editar}** atualizados para **{effective_new_name}** ({effective_new_funcao}).")
                        # Clear inputs after saving
                        st.session_state.edit_selected_name = ""
                        st.session_state.edit_new_name_val = ""
                        st.session_state.edit_new_funcao_val = ""
                        st.rerun()
                    else:
                        st.error(f"❌ Não foi possível atualizar **{colab_para_editar}**. O novo nome pode já existir ou houve um erro.")
                else:
                    st.warning("⚠️ Por favor, selecione um colaborador para editar.")

    # --- Remover Colaborador ---
    with st.expander("🗑️ Remover Colaborador"):
        st.markdown("Cuidado! Esta ação é irreversível.")
        df_colab_atual = carregar_colaboradores()
        nomes_para_remover = [""] + df_colab_atual["Nome"].tolist()
        
        # Use st.session_state to manage selectbox value
        if 'remove_select_box_key' not in st.session_state:
            st.session_state.remove_select_box_key = ""
        if 'confirm_remove_checkbox_key' not in st.session_state:
            st.session_state.confirm_remove_checkbox_key = False

        with st.form("form_remove_colaborador"):
            nome_remover = st.selectbox(
                "🗑️ **Selecione o nome para remover:**", 
                nomes_para_remover, 
                key="remove_select_box_form"
            )
            confirmar = st.checkbox(
                "Confirmo que desejo remover este colaborador permanentemente.", 
                key="confirm_remove_checkbox_form"
            )
            submitted_remove = st.form_submit_button("Remover Colaborador 🛑")

            if submitted_remove:
                if nome_remover:
                    if confirmar:
                        if remover_colaborador(nome_remover):
                            st.warning(f"🗑️ Colaborador **{nome_remover}** foi removido com sucesso!")
                            # Clear the selectbox and checkbox state
                            st.session_state.remove_select_box_key = ""
                            st.session_state.confirm_remove_checkbox_key = False
                            st.rerun() # Rerun to clear selectbox and checkbox
                        else:
                            st.error(f"❌ Erro ao remover o colaborador **{nome_remover}**.")
                    else:
                        st.info("ℹ️ Marque a caixa de confirmação antes de remover o colaborador.")
                else:
                    st.warning("⚠️ Por favor, selecione um colaborador para remover.")

    st.markdown("---")
    st.subheader("📃 Lista Atual de Colaboradores")
    df_colab_final = carregar_colaboradores()
    if not df_colab_final.empty:
        st.dataframe(df_colab_final, use_container_width=True)
    else:
        st.info("Nenhum colaborador cadastrado ainda.")

elif aba == "Relatórios":
    st.header("📊 Relatórios de Ponto")
    st.markdown("Visualize o histórico de ponto e o cálculo de horas trabalhadas por data.")

    st.subheader("📅 Histórico Detalhado por Data")
    col_date, col_name_report = st.columns([1, 2])
    with col_date:
        data_relatorio = st.date_input("🗓️ Escolha uma data:", datetime.today(), key="rel_date_input")
    with col_name_report:
        df_colab_report = carregar_colaboradores()
        nomes_relatorio = ["Todos"] + df_colab_report["Nome"].tolist()
        colab_relatorio = st.selectbox("👤 Filtrar por Colaborador:", nomes_relatorio, key="rel_colab_select")

    df_pontos_full = carregar_pontos()
    
    # Filter by date
    df_dia = df_pontos_full[df_pontos_full["Data"] == data_relatorio.strftime("%Y-%m-%d")]
    
    # Filter by collaborator if "Todos" is not selected
    if colab_relatorio != "Todos":
        df_dia = df_dia[df_dia["Nome"] == colab_relatorio]

    st.write(f"🧾 **Registros de Ponto para {data_relatorio.strftime('%d/%m/%Y')}**:")
    if not df_dia.empty:
        st.dataframe(df_dia.sort_values(by=["Nome", "Hora"]), use_container_width=True)
        csv_registros = df_dia.to_csv(index=False, sep=';', decimal=',').encode("utf-8") # Use semicolon as separator
        st.download_button(
            "📥 Baixar Registros Detalhados (CSV)",
            data=csv_registros,
            file_name=f"registros_ponto_detalhado_{data_relatorio.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Baixa todos os registros de ponto do dia selecionado."
        )
    else:
        st.info("Nenhum registro encontrado para a data e filtro selecionados.")

    st.markdown("---")
    st.subheader("🕒 Cálculo de Horas Trabalhadas (Diário por Colaborador)")
    st.markdown("As horas são calculadas da primeira 'Entrada' até a última 'Saída' para cada colaborador no dia.")
    
    # Calculate hours for the selected date
    df_horas = calcular_horas(df_pontos_full[df_pontos_full["Data"] == data_relatorio.strftime("%Y-%m-%d")])
    
    # If a specific collaborator is selected for report, filter the hours dataframe too
    if colab_relatorio != "Todos":
        df_horas = df_horas[df_horas["Nome"] == colab_relatorio]


    if not df_horas.empty:
        st.dataframe(df_horas, use_container_width=True)
        
        # Calculate total hours for the displayed dataframe
        total_horas_dia = timedelta(0)
        for _, row in df_horas.iterrows():
            if row["Horas Trabalhadas"] not in ["Incompleto / Sem Saída Válida", "Incompleto"]:
                h, m, s = map(int, row["Horas Trabalhadas"].split(':'))
                total_horas_dia += timedelta(hours=h, minutes=m, seconds=s)
        
        # Format total hours
        total_seconds = int(total_horas_dia.total_seconds())
        total_h, remainder = divmod(total_seconds, 3600)
        total_m, total_s = divmod(remainder, 60)
        
        st.markdown(f"**⏰ Total de Horas Trabalhadas (Dia):** `{total_h:02}:{total_m:02}:{total_s:02}`")

        # Prepare DataFrame for download, including the total if desired
        df_horas_para_csv = df_horas.copy()
        
        # Add a "Total" row to the CSV data if it's meaningful for the specific report
        # For this daily report, the total is already shown above.
        # If you want a row at the bottom of the CSV, it's a bit more complex for standard CSV readers.
        # A simpler way is to just include the formatted total in the filename or a separate report.
        
        csv_horas_trabalhadas = df_horas_para_csv.to_csv(index=False, sep=';', decimal=',').encode("utf-8")
        st.download_button(
            "📥 Baixar Cálculo de Horas (CSV)",
            data=csv_horas_trabalhadas,
            file_name=f"horas_trabalhadas_diarias_{data_relatorio.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Baixa as horas trabalhadas calculadas para o dia selecionado."
        )
    else:
        st.info("Nenhum cálculo de horas disponível para a data e filtro selecionados.")

elif aba == "Ajustar Ponto":
    st.header("⚙️ Ajuste Manual de Registros de Ponto")
    st.markdown("Ferramenta para administradores ajustarem ou corrigirem registros de ponto.")
    
    df_colab_ajuste = carregar_colaboradores()
    nomes_ajuste = [""] + df_colab_ajuste["Nome"].tolist()
    
    col_ajuste_sel, col_ajuste_date = st.columns(2)
    with col_ajuste_sel:
        colab_selecionado = st.selectbox(
            "👤 **Selecione o Colaborador:**", 
            nomes_ajuste, 
            key="ajustar_colab_select_main"
        )
    with col_ajuste_date:
        data_ajuste = st.date_input(
            "🗓️ **Selecione a Data do Ajuste:**", 
            datetime.today(), 
            key="ajustar_date_input_main"
        )
    
    if colab_selecionado:
        df_pontos = carregar_pontos()
        registros_do_dia = df_pontos[
            (df_pontos["Nome"] == colab_selecionado) & 
            (df_pontos["Data"] == data_ajuste.strftime("%Y-%m-%d"))
        ].sort_values(by="Hora").reset_index() # Keep original index in a column
        
        st.markdown(f"#### 📋 Registros para **{colab_selecionado}** em **{data_ajuste.strftime('%d/%m/%Y')}**")
        st.warning("🚨 **Atenção:** As alterações aqui são diretas nos dados. Tenha certeza antes de salvar.")
        
        if registros_do_dia.empty:
            st.info("Nenhum registro encontrado para esta data e colaborador. Você pode adicionar manualmente abaixo.")
        else:
            for i, row in registros_do_dia.iterrows():
                original_index = row['index'] # Get the original index from the DataFrame
                
                with st.container(border=True):
                    st.markdown(f"**Registro #{i+1} (ID original: `{original_index}`):**")
                    col_acao, col_data, col_hora = st.columns(3)
                    
                    with col_acao:
                        novo_acao = st.selectbox(
                            "Ação", 
                            ["Entrada", "Pausa", "Retorno", "Saída"], 
                            index=["Entrada", "Pausa", "Retorno", "Saída"].index(row["Ação"]),
                            key=f"ajust_acao_{original_index}"
                        )
                    with col_data:
                        novo_data_str = st.text_input(
                            "Data (YYYY-MM-DD)", 
                            value=row["Data"], 
                            key=f"ajust_data_{original_index}"
                        ).strip()
                    with col_hora:
                        novo_hora_str = st.text_input(
                            "Hora (HH:MM:SS)", 
                            value=row["Hora"], 
                            key=f"ajust_hora_{original_index}"
                        ).strip()
                    
                    col_update, col_delete = st.columns(2)
                    with col_update:
                        if st.button(f"Salvar Ajuste {i+1} ✅", use_container_width=True, key=f"update_btn_{original_index}"):
                            try:
                                datetime.strptime(novo_data_str, "%Y-%m-%d")
                                datetime.strptime(novo_hora_str, "%H:%M:%S")
                                
                                if atualizar_ponto(original_index, colab_selecionado, novo_acao, novo_data_str, novo_hora_str):
                                    st.success(f"Registro {i+1} atualizado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao atualizar o registro.")
                            except ValueError:
                                st.error("❌ Formato de Data (YYYY-MM-DD) ou Hora (HH:MM:SS) inválido.")
                    with col_delete:
                        if st.button(f"Excluir Registro {i+1} 🗑️", use_container_width=True, key=f"delete_btn_{original_index}"):
                            if deletar_ponto(original_index):
                                st.warning(f"Registro {i+1} excluído.")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao excluir o registro.")
                st.markdown("---") # Separator for each record

        st.markdown("### ➕ Adicionar Novo Registro para este Colaborador/Data")
        st.info("Use para adicionar entradas ou saídas que faltaram.")
        with st.form("form_add_ponto_manual"):
            col_add_acao, col_add_data, col_add_hora = st.columns(3)
            with col_add_acao:
                acao_manual = st.selectbox(
                    "Ação", 
                    ["Entrada", "Pausa", "Retorno", "Saída"], 
                    key="add_manual_acao"
                )
            with col_add_data:
                data_manual_str = st.text_input(
                    "Data (YYYY-MM-DD)", 
                    value=data_ajuste.strftime("%Y-%m-%d"), 
                    key="add_manual_data"
                ).strip()
            with col_add_hora:
                hora_manual_str = st.text_input(
                    "Hora (HH:MM:SS)", 
                    value=datetime.now().strftime("%H:%M:%S"), 
                    key="add_manual_hora"
                ).strip()
            
            submitted_add_manual = st.form_submit_button("Adicionar Novo Registro ✨")
            
            if submitted_add_manual:
                try:
                    datetime.strptime(data_manual_str, "%Y-%m-%d")
                    datetime.strptime(hora_manual_str, "%H:%M:%S")
                    
                    # Instead of calling salvar_ponto (which uses now()), manually add to df_pontos
                    # and save the full dataframe.
                    agora_manual = datetime.strptime(f"{data_manual_str} {hora_manual_str}", "%Y-%m-%d %H:%M:%S")
                    data_salvar = agora_manual.strftime("%Y-%m-%d")
                    hora_salvar = agora_manual.strftime("%H:%M:%S")

                    novo_manual = pd.DataFrame([[colab_selecionado, acao_manual, data_salvar, hora_salvar]], 
                                            columns=["Nome", "Ação", "Data", "Hora"])
                    df_pontos_full = carregar_pontos()
                    df_pontos_full = pd.concat([df_pontos_full, novo_manual], ignore_index=True)
                    df_pontos_full.to_csv(ARQ_PONTO, index=False)
                    
                    st.success("✅ Novo registro de ponto adicionado manualmente!")
                    st.rerun()
                except ValueError:
                    st.error("❌ Formato de Data (YYYY-MM-DD) ou Hora (HH:MM:SS) inválido.")
    else:
        st.info("Selecione um colaborador e uma data para visualizar e ajustar os registros de ponto.")