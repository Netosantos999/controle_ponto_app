import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import holidays

# --- Configurações do Aplicativo ---
st.set_page_config(
    page_title="Controle de Ponto",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:francelinotees@gmail.com',
        'Report a bug': 'mailto:francelinotees@gmail.com',
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

    df_pontos = carregar_pontos()

    duplicado_exato = df_pontos[
        (df_pontos["Nome"] == nome) &
        (df_pontos["Ação"] == acao) &
        (df_pontos["Data"] == data_str) &
        (df_pontos["Hora"] == hora_str)
    ]

    if not duplicado_exato.empty:
        st.warning(f"Registro já existe: {nome} - {acao} em {data_str} às {hora_str}")
        return False

    df_mesmo_dia = df_pontos[
        (df_pontos["Nome"] == nome) &
        (df_pontos["Ação"] == acao) &
        (df_pontos["Data"] == data_str)
    ]

    hora_nova = datetime.strptime(hora_str, "%H:%M")
    for _, row in df_mesmo_dia.iterrows():
        try:
            hora_existente = datetime.strptime(str(row["Hora"])[:5], "%H:%M")
            diferenca = abs((hora_existente - hora_nova).total_seconds())
            if diferenca < 60:
                st.warning(f"Registro ignorado: ação semelhante registrada há menos de 1 minuto ({row['Hora']}).")
                return False
        except:
            continue

    novo_registro = pd.DataFrame([[nome, acao, data_str, hora_str]], columns=["Nome", "Ação", "Data", "Hora"])
    df_pontos = pd.concat([df_pontos, novo_registro], ignore_index=True)
    df_pontos.to_csv(ARQ_PONTO, index=False)
    return True

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
    df["DataHora"] = pd.to_datetime(df["Data"] + " " + df["Hora"], format="%Y-%m-%d %H:%M")
    df = df.sort_values(by=["Nome", "DataHora"])

    nomes = df["Nome"].unique()

    for nome in nomes:
        df_nome = df[df["Nome"] == nome].sort_values("DataHora").reset_index(drop=True)
        i = 0

        while i < len(df_nome):
            row = df_nome.iloc[i]
            if row["Ação"] == "Entrada":
                data_entrada = row["Data"]
                hora_entrada = row["DataHora"]

                if i + 1 < len(df_nome) and df_nome.iloc[i + 1]["Ação"] == "Saída":
                    hora_saida = df_nome.iloc[i + 1]["DataHora"]
                    if hora_saida < hora_entrada:
                        hora_saida += timedelta(days=1)

                    duracao = hora_saida - hora_entrada
                    total_segundos = int(duracao.total_seconds())
                    horas, resto = divmod(total_segundos, 3600)
                    minutos, _ = divmod(resto, 60)
                    tempo_formatado = f"{int(horas):02}:{int(minutos):02}"
                    resultado.append((nome, data_entrada, tempo_formatado))
                    i += 2

                elif (
                    i + 3 < len(df_nome) and
                    df_nome.iloc[i + 1]["Ação"] == "Pausa" and
                    df_nome.iloc[i + 2]["Ação"] == "Retorno" and
                    df_nome.iloc[i + 3]["Ação"] == "Saída"
                ):
                    h1 = df_nome.iloc[i]["DataHora"]
                    h2 = df_nome.iloc[i + 1]["DataHora"]
                    h3 = df_nome.iloc[i + 2]["DataHora"]
                    h4 = df_nome.iloc[i + 3]["DataHora"]
                    duracao = (h2 - h1) + (h4 - h3)

                    total_segundos = int(duracao.total_seconds())
                    horas, resto = divmod(total_segundos, 3600)
                    minutos, _ = divmod(resto, 60)
                    tempo_formatado = f"{int(horas):02}:{int(minutos):02}"
                    resultado.append((nome, data_entrada, tempo_formatado))
                    i += 4

                else:
                    resultado.append((nome, data_entrada, "Registro Incompleto"))
                    i += 1
            else:
                i += 1

    return pd.DataFrame(resultado, columns=["Nome", "Data", "Horas Trabalhadas"])

def formatar_timedelta(td):
    total_segundos = int(td.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    return f"{horas:02}:{minutos:02}"

def calcular_horas_extras(df_colaborador):
    extras_50 = timedelta()
    extras_100 = timedelta()
    
    br_holidays = holidays.Brazil(state='CE')

    df_colaborador["DataHora"] = pd.to_datetime(
        df_colaborador["Data"] + " " + df_colaborador["Hora"],
        format="%Y-%m-%d %H:%M",
        errors='coerce'
    )
    df_colaborador = df_colaborador.dropna(subset=["DataHora"])
    df_colaborador = df_colaborador.sort_values(by="DataHora").reset_index(drop=True)

    i = 0
    while i < len(df_colaborador):
        row = df_colaborador.iloc[i]
        if row["Ação"] == "Entrada":
            periodos_trabalho = []
            
            if i + 1 < len(df_colaborador) and df_colaborador.iloc[i + 1]["Ação"] == "Saída":
                periodos_trabalho.append((row["DataHora"], df_colaborador.iloc[i + 1]["DataHora"]))
                i += 2
            elif (i + 3 < len(df_colaborador) and
                  df_colaborador.iloc[i + 1]["Ação"] == "Pausa" and
                  df_colaborador.iloc[i + 2]["Ação"] == "Retorno" and
                  df_colaborador.iloc[i + 3]["Ação"] == "Saída"):
                periodos_trabalho.append((row["DataHora"], df_colaborador.iloc[i + 1]["DataHora"]))
                periodos_trabalho.append((df_colaborador.iloc[i + 2]["DataHora"], df_colaborador.iloc[i + 3]["DataHora"]))
                i += 4
            else:
                i += 1
                continue

            for inicio, fim in periodos_trabalho:
                data_corrente = inicio
                while data_corrente.date() <= fim.date():
                    data_atual = data_corrente.date()
                    dia_semana = data_atual.weekday()
                    
                    inicio_calculo = max(data_corrente, inicio)
                    fim_do_dia = pd.to_datetime(data_atual) + timedelta(days=1)
                    fim_calculo = min(fim_do_dia, fim)

                    if inicio_calculo >= fim:
                        break
                    
                    duracao_no_dia = fim_calculo - inicio_calculo
                    
                    if data_atual in br_holidays:
                        extras_100 += duracao_no_dia
                    elif dia_semana == 6: # Domingo
                        extras_100 += duracao_no_dia
                    elif dia_semana == 5: # Sábado
                        extras_50 += duracao_no_dia
                    elif dia_semana == 4: # Sexta-feira
                        limite = data_corrente.replace(hour=16, minute=0, second=0, microsecond=0)
                        if fim_calculo > limite:
                            inicio_extra = max(inicio_calculo, limite)
                            extras_50 += (fim_calculo - inicio_extra)
                    elif 0 <= dia_semana <= 3: # Segunda a Quinta
                        limite = data_corrente.replace(hour=17, minute=0, second=0, microsecond=0)
                        if fim_calculo > limite:
                            inicio_extra = max(inicio_calculo, limite)
                            extras_50 += (fim_calculo - inicio_extra)

                    data_corrente = pd.to_datetime(data_atual + timedelta(days=1))
        else:
            i += 1
            
    return {
        "50%": extras_50,
        "100%": extras_100,
    }

# --- Inicialização ---
inicializar_arquivos()

# --- Interface Principal ---
st.title("Controle de Ponto")
st.markdown("Sistema para registro e gerenciamento de ponto dos colaboradores.")

aba = st.sidebar.radio("Navegação", ["Registrar Ponto", "Gerenciar Colaboradores", "Relatórios", "Ajustar Ponto"])

if aba == "Registrar Ponto":
    st.header("Registro de Ponto")
    st.markdown("Informe manualmente a data e hora da entrada. O sistema registrará automaticamente:")
    st.markdown("- Pausa às 12:00")
    st.markdown("- Retorno às 13:00")
    st.markdown("- Saída às 17:00 (segunda a quinta) ou 16:00 (sexta)")
    st.markdown("- Os Vigias tem Botões espercificos")

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
                datetime.strptime(hora_input, "%H:%M")
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
                
                st.markdown("🌙 vigia da noite? Use o botão abaixo para registrar das 18:00 às 06:00 do dia seguinte.")

                if st.button("Registrar Turno Noturno (18:00 - 06:00)", use_container_width=True):
                    registrar_evento(nome_selecionado, "Entrada", data_str, "18:00")
                    data_saida = (datetime.strptime(data_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                    registrar_evento(nome_selecionado, "Saída", data_saida, "06:00")
                    st.success(
                        f"Turno noturno registrado: entrada às 18:00 em {data_str} e saída às 06:00 em {data_saida}."
                    )

                st.markdown("🌞 Vigia do dia? Use o botão abaixo para registrar das 06:00 às 18:00 no mesmo dia.")

                if st.button("Registrar Turno Diurno (06:00 - 18:00)", use_container_width=True):
                   registrar_evento(nome_selecionado, "Entrada", data_str, "06:00")
                   registrar_evento(nome_selecionado, "Saída", data_str, "18:00")
                   st.success(
                     f"Turno diurno registrado: entrada às 06:00 e saída às 18:00 em {data_str}."
                   )
            except ValueError:
                st.error("Horario atual")
        else:
            st.warning("Por favor, selecione um nome.")

elif aba == "Gerenciar Colaboradores":
    st.header("Gerenciar Colaboradores")
    df_colab = carregar_colaboradores()
    with st.form("form_add_colaborador"):
        st.subheader("Adicionar Novo Colaborador")
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome completo")
        funcao = col2.text_input("Função ou cargo")
        if st.form_submit_button("Adicionar"):
            if nome.strip():
                if adicionar_colaborador(nome.strip(), funcao.strip()):
                    st.success("Colaborador adicionado com sucesso.")
                    st.rerun()
                else:
                    st.warning("Este nome já está cadastrado.")
            else:
                st.error("O campo de nome é obrigatório.")
    st.markdown("---")
    st.subheader("Lista de Colaboradores")
    if df_colab.empty:
        st.info("Nenhum colaborador cadastrado.")
    else:
        funcoes = sorted([f for f in df_colab["Funcao"].dropna().unique() if f])
        for funcao in funcoes:
            colab_funcao = df_colab[df_colab["Funcao"] == funcao]
            st.markdown(f"#### {funcao}")
            for i, row in colab_funcao.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([4, 4, 2])
                    col1.write(f"Nome: {row['Nome']}")
                    col2.write(f"Função: {row['Funcao']}")
                    if col3.button("Excluir", key=f"excluir_{i}", use_container_width=True):
                        if remover_colaborador(row["Nome"]):
                            st.warning(f"Colaborador '{row['Nome']}' removido.")
                            st.rerun()
                with st.expander("Editar"):
                    col1, col2, col3 = st.columns([4, 4, 2])
                    novo_nome = col1.text_input("Novo nome", value=row["Nome"], key=f"novo_nome_{i}")
                    nova_funcao = col2.text_input("Nova função", value=row["Funcao"], key=f"nova_funcao_{i}")
                    if col3.button("Salvar", key=f"salvar_edicao_{i}", use_container_width=True):
                        if novo_nome.strip():
                            if editar_colaborador(row["Nome"], novo_nome.strip(), nova_funcao.strip()):
                                st.success("Dados atualizados com sucesso.")
                                st.rerun()
                            else:
                                st.error("Não foi possível atualizar. Verifique se o novo nome já existe.")
                        else:
                            st.error("O nome não pode estar vazio.")

elif aba == "Relatórios":
    st.header("Relatórios de Ponto")
    st.markdown("Visualize o histórico de ponto, total de horas e baixe os arquivos.")
    df_pontos = carregar_pontos()
    df_colab = carregar_colaboradores()
    
    if df_pontos.empty or df_colab.empty:
        st.warning("Sem dados suficientes para gerar relatórios.")
    else:
        col1, col2 = st.columns(2)
        data_inicio = col1.date_input("Data inicial", value=datetime.today().replace(day=1), key="relatorio_inicio")
        data_fim = col2.date_input("Data final", value=datetime.today(), key="relatorio_fim")

        st.markdown("---")

        st.subheader("Quantitativo por Função")
        if not df_colab.empty:
            contagem_funcao = df_colab['Funcao'].value_counts().reset_index()
            contagem_funcao.columns = ['Função', 'Quantidade']
            st.dataframe(contagem_funcao, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum colaborador cadastrado para exibir o quantitativo.")
        
        st.markdown("---")

        # --- BLOCO DE RELATÓRIO DE FALTAS APRIMORADO ---
        st.subheader("Relatório de Faltas")
        st.markdown("Exibe os dias úteis (Seg-Sex, exceto feriados) em que não houve registro de 'Entrada' para o colaborador no período selecionado.")

        colabs_normais = df_colab[~df_colab['Funcao'].str.contains("vigia", case=False, na=False)]
        nomes_esperados_lista = ["Todos"] + sorted(colabs_normais['Nome'].unique().tolist())
        
        colab_falta_selecionado = st.selectbox(
            "Filtrar por Colaborador:",
            nomes_esperados_lista,
            key="falta_colab_select"
        )
        
        br_holidays = holidays.Brazil(state='CE')
        datas_periodo = pd.date_range(start=data_inicio, end=data_fim)
        
        dias_uteis = [data for data in datas_periodo if data.weekday() < 5 and data not in br_holidays]
        
        if not dias_uteis:
            st.info("Não há dias úteis no período selecionado para verificar faltas.")
        else:
            faltas_por_colaborador = {nome: [] for nome in colabs_normais['Nome']}
            
            for data in dias_uteis:
                data_str = data.strftime("%Y-%m-%d")
                presentes_no_dia = set(df_pontos[
                    (df_pontos['Data'] == data_str) & 
                    (df_pontos['Ação'] == 'Entrada')
                ]['Nome'])
                
                for nome in faltas_por_colaborador:
                    if nome not in presentes_no_dia:
                        faltas_por_colaborador[nome].append(data.strftime('%d/%m/%Y'))

            # Filtrar dicionário para manter apenas colaboradores com faltas
            faltas_por_colaborador = {nome: datas for nome, datas in faltas_por_colaborador.items() if datas}

            if not faltas_por_colaborador:
                st.success("Nenhuma falta registrada para o período e filtro selecionados.")
            else:
                if colab_falta_selecionado == "Todos":
                    st.error("Foram encontradas as seguintes faltas no período:")
                    for nome, datas_faltas in sorted(faltas_por_colaborador.items()):
                        with st.expander(f"**{nome}** - {len(datas_faltas)} falta(s)"):
                            for data_falta in datas_faltas:
                                st.markdown(f"- {data_falta}")
                else:
                    if colab_falta_selecionado in faltas_por_colaborador:
                        st.error(f"O colaborador **{colab_falta_selecionado}** faltou nos seguintes dias:")
                        datas_ausencia = faltas_por_colaborador[colab_falta_selecionado]
                        for data_falta in datas_ausencia:
                            st.markdown(f"- {data_falta}")
                    else:
                        st.success(f"Nenhuma falta encontrada para **{colab_falta_selecionado}** no período selecionado.")
        
        st.markdown("---")

        st.subheader("Resumo Geral de Horas Extras no Período")
        
        resumo_extras = []
        df_pontos_periodo_geral = df_pontos[
            (pd.to_datetime(df_pontos["Data"]) >= pd.to_datetime(data_inicio)) &
            (pd.to_datetime(df_pontos["Data"]) <= pd.to_datetime(data_fim))
        ]

        for _, colaborador in df_colab.iterrows():
            nome_colab = colaborador["Nome"]
            funcao_colab = colaborador["Funcao"]
            
            if "vigia" in str(funcao_colab).lower():
                continue

            df_pontos_colaborador = df_pontos_periodo_geral[df_pontos_periodo_geral["Nome"] == nome_colab]
            
            if not df_pontos_colaborador.empty:
                resultado_extras = calcular_horas_extras(df_pontos_colaborador.copy())
                he_50 = resultado_extras.get("50%", timedelta())
                he_100 = resultado_extras.get("100%", timedelta())

                if he_50.total_seconds() > 0 or he_100.total_seconds() > 0:
                    resumo_extras.append({
                        "Nome": nome_colab,
                        "Horas Extras (50%)": formatar_timedelta(he_50),
                        "Horas Extras (100%)": formatar_timedelta(he_100)
                    })
        
        if resumo_extras:
            df_resumo = pd.DataFrame(resumo_extras)
            st.dataframe(df_resumo, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum colaborador com horas extras encontradas no período selecionado.")
        
        st.markdown("---")

        st.subheader("Análise Individual por Colaborador")
        nomes_disponiveis = df_colab["Nome"].unique().tolist()
        colab_filtrado = st.selectbox("Selecionar colaborador:", nomes_disponiveis, key="relatorio_nome_total")
        
        df_calculado_completo = calcular_horas(df_pontos[df_pontos["Nome"] == colab_filtrado])
        df_calculado = df_calculado_completo[
            (pd.to_datetime(df_calculado_completo["Data"]) >= pd.to_datetime(data_inicio)) &
            (pd.to_datetime(df_calculado_completo["Data"]) <= pd.to_datetime(data_fim))
        ]
        
        if not df_calculado.empty:
            st.write("**Total de Horas Trabalhadas**")
            st.dataframe(df_calculado, use_container_width=True)
            total_segundos = 0
            for tempo in df_calculado["Horas Trabalhadas"]:
                if tempo != "Registro Incompleto":
                    h, m = map(int, tempo.split(":"))
                    total_segundos += h * 3600 + m * 60
            horas_total = total_segundos // 3600
            minutos_total = (total_segundos % 3600) // 60
            st.success(f"Total de horas trabalhadas no período: {horas_total:02}:{minutos_total:02}")
            
            st.markdown("---")
            st.write("**Cálculo de Horas Extras no Período**")
            funcao_colaborador = df_colab.loc[df_colab["Nome"] == colab_filtrado, "Funcao"].iloc[0]
            if "vigia" in str(funcao_colaborador).lower():
                st.info(f"Colaboradores na função de '{funcao_colaborador}' não são elegíveis para horas extras.")
            else:
                df_pontos_periodo_individual = df_pontos_periodo_geral[df_pontos_periodo_geral["Nome"] == colab_filtrado]

                if not df_pontos_periodo_individual.empty:
                    resultado_extras_individual = calcular_horas_extras(df_pontos_periodo_individual.copy())
                    he_50 = resultado_extras_individual.get("50%", timedelta())
                    he_100 = resultado_extras_individual.get("100%", timedelta())
                    col_he1, col_he2 = st.columns(2)
                    with col_he1:
                        st.metric(label="Horas Extras (50%)", value=formatar_timedelta(he_50))
                    with col_he2:
                        st.metric(label="Horas Extras (100%)", value=formatar_timedelta(he_100))
                    
                    with st.expander("Ver regras de cálculo de Horas Extras"):
                        st.markdown("""
                        - **Feriados:** Todas as horas trabalhadas são calculadas a 100%.
                        - **Domingo:** Todas as horas trabalhadas são calculadas a 100%.
                        - **Sábado:** Todas as horas trabalhadas são calculadas a 50%.
                        - **Sexta-feira:** Horas trabalhadas após as 16:00 são calculadas a 50%.
                        - **Segunda a Quinta:** Horas trabalhadas após as 17:00 são calculadas a 50%.
                        """)
                else:
                    st.info("Nenhum registro de ponto encontrado para o cálculo de horas extras deste colaborador no período.")
        else:
            st.info("Nenhum registro encontrado para o colaborador no período selecionado.")
        
        st.markdown("---")
        st.subheader("Histórico Detalhado por Data")
        col_date, col_name_report = st.columns([1, 2])
        with col_date:
            data_relatorio = st.date_input("Selecione uma data:", datetime.today(), key="rel_date_input")
        with col_name_report:
            nomes_relatorio = ["Todos"] + df_colab["Nome"].tolist()
            colab_relatorio = st.selectbox("Filtrar por Colaborador:", nomes_relatorio, key="rel_colab_select")
        
        df_dia = df_pontos[df_pontos["Data"] == data_relatorio.strftime("%Y-%m-%d")]
        if colab_relatorio != "Todos":
            df_dia = df_dia[df_dia["Nome"] == colab_relatorio]
        
        st.write(f"Registros de Ponto para {data_relatorio.strftime('%d/%m/%Y')}:")
        if not df_dia.empty:
            st.dataframe(df_dia.sort_values(by=["Nome", "Hora"]), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado para a data e filtro selecionados.")
        
        st.markdown("---")
        st.subheader("Resumo de Horas Totais por Funcionário no Período")
        st.write(f"Exibindo o total de horas trabalhadas por cada funcionário entre **{data_inicio.strftime('%d/%m/%Y')}** e **{data_fim.strftime('%d/%m/%Y')}**.")

        df_pontos_periodo_resumo = df_pontos[
            (pd.to_datetime(df_pontos["Data"]) >= pd.to_datetime(data_inicio)) &
            (pd.to_datetime(df_pontos["Data"]) <= pd.to_datetime(data_fim))
        ]

        if not df_pontos_periodo_resumo.empty:
            df_horas_diarias = calcular_horas(df_pontos_periodo_resumo.copy())
            df_validas = df_horas_diarias[df_horas_diarias['Horas Trabalhadas'] != 'Registro Incompleto'].copy()

            if not df_validas.empty:
                def hms_to_seconds(t):
                    try:
                        h, m = map(int, t.split(':'))
                        return (h * 3600) + (m * 60)
                    except (ValueError, TypeError):
                        return 0
                
                df_validas['Segundos'] = df_validas['Horas Trabalhadas'].apply(hms_to_seconds)
                resumo_segundos = df_validas.groupby('Nome')['Segundos'].sum().reset_index()

                def seconds_to_hms(s):
                    s = int(s)
                    horas = s // 3600
                    minutos = (s % 3600) // 60
                    return f"{horas:02}:{minutos:02}"

                resumo_segundos['Total de Horas'] = resumo_segundos['Segundos'].apply(seconds_to_hms)
                df_resumo_final = resumo_segundos[['Nome', 'Total de Horas']]
                st.dataframe(df_resumo_final, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro de hora completo encontrado no período para gerar o resumo.")
        else:
            st.info("Nenhum registro de ponto encontrado no período selecionado.")
        
        st.markdown("---")
        st.subheader("Exportar Registros")
        st.download_button(
            label="Baixar Registros de Ponto (registro_ponto.csv)",
            data=df_pontos.to_csv(index=False).encode('utf-8'),
            file_name='registro_ponto.csv',
            mime='text/csv'
        )
        st.download_button(
            label="Baixar Lista de Colaboradores (colaboradores.csv)",
            data=df_colab.to_csv(index=False).encode('utf-8'),
            file_name='colaboradores.csv',
            mime='text/csv'
        )

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
        df_pontos_ajuste = carregar_pontos()
        registros_do_dia = df_pontos_ajuste[
            (df_pontos_ajuste["Nome"] == colab_selecionado) & 
            (df_pontos_ajuste["Data"] == data_ajuste.strftime("%Y-%m-%d"))
        ].sort_values(by="Hora").reset_index()
        
        st.markdown(f"#### Registros para **{colab_selecionado}** em **{data_ajuste.strftime('%d/%m/%Y')}**")
        
        if not registros_do_dia.empty:
            for i, row in registros_do_dia.iterrows():
                original_index = row['index']
                with st.container(border=True):
                    st.markdown(f"**Registro ID `{original_index}`:**")
                    col_acao, col_data, col_hora = st.columns(3)
                    
                    acoes_ponto = ["Entrada", "Pausa", "Retorno", "Saída"]
                    index_acao = acoes_ponto.index(row["Ação"]) if row["Ação"] in acoes_ponto else 0
                    
                    novo_acao = col_acao.selectbox("Ação", acoes_ponto, index=index_acao, key=f"ajust_acao_{original_index}")
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
                    if registrar_evento(colab_selecionado, acao_manual, data_manual_str, hora_manual_str):
                        st.success("Novo registro manual adicionado com sucesso.")
                        st.rerun()
                except ValueError:
                    st.error("Formato de Data (YYYY-MM-DD) ou Hora (HH:MM) inválido.")
    else:
        st.info("Selecione um colaborador e uma data para visualizar e ajustar os registros.")
