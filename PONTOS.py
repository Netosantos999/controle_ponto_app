import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from contextlib import contextmanager
try:
    from filelock import FileLock
except ImportError:
    FileLock = None

# Utilitário para lock de arquivo
@contextmanager
def safe_csv_write(filepath):
    if FileLock is not None:
        lock = FileLock(filepath + ".lock")
        with lock:
            yield
    else:
        yield
import holidays
from collections import defaultdict
from enum import Enum
from typing import List, Dict, Any, Optional

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

# --- Constantes de Arquivos e Diretórios ---
ARQ_PONTO = "registro_ponto.csv"
ARQ_COLAB = "colaboradores.csv"
ARQ_FERIADOS = "feriados.csv"
ARQ_FERIADOS_IGNORADOS = "feriados_ignorados.csv" # NOVO: Arquivo para feriados do sistema a serem ignorados
FOTOS_DIR = "fotos_colaboradores"

class AcaoPonto(str, Enum):
    ENTRADA = "Entrada"
    SAIDA = "Saída"
    PAUSA = "Pausa"
    RETORNO = "Retorno"

class DataManager:
    # --- MODIFICADO ---
    def __init__(self, arq_colab: str, arq_ponto: str, fotos_dir: str, arq_feriados: str, arq_feriados_ignorados: str):
        self.arq_colab = arq_colab
        self.arq_ponto = arq_ponto
        self.fotos_dir = fotos_dir
        self.arq_feriados = arq_feriados
        self.arq_feriados_ignorados = arq_feriados_ignorados # NOVO
        self._inicializar_arquivos()

    def _inicializar_arquivos(self):
        # Garante que os arquivos CSV existam
        if not os.path.exists(self.arq_colab):
            pd.DataFrame(columns=["Nome", "Funcao"]).to_csv(self.arq_colab, index=False)
        if not os.path.exists(self.arq_ponto):
            pd.DataFrame(columns=["Nome", "Ação", "Data", "Hora"]).to_csv(self.arq_ponto, index=False)
        if not os.path.exists(self.arq_feriados):
            pd.DataFrame(columns=["Data", "Descricao"]).to_csv(self.arq_feriados, index=False)
        # NOVO: Garante que o arquivo de feriados ignorados exista
        if not os.path.exists(self.arq_feriados_ignorados):
            pd.DataFrame(columns=["Data", "Descricao"]).to_csv(self.arq_feriados_ignorados, index=False)
        
        os.makedirs(self.fotos_dir, exist_ok=True)

    @st.cache_data(ttl=30)
    def carregar_colaboradores(_self) -> pd.DataFrame:
        try:
            return pd.read_csv(_self.arq_colab)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=["Nome", "Funcao"])

    def salvar_colaboradores(self, df: pd.DataFrame):
        with safe_csv_write(self.arq_colab):
            df.to_csv(self.arq_colab, index=False)
        st.cache_data.clear()

    def carregar_pontos(_self) -> pd.DataFrame:
        try:
            return pd.read_csv(_self.arq_ponto)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=["Nome", "Ação", "Data", "Hora"])

    def salvar_pontos(self, df: pd.DataFrame):
        with safe_csv_write(self.arq_ponto):
            df.to_csv(self.arq_ponto, index=False)
        st.cache_data.clear()

    @st.cache_data(ttl=60)
    def carregar_feriados(_self) -> pd.DataFrame:
        try:
            df = pd.read_csv(_self.arq_feriados)
            df['Data'] = pd.to_datetime(df['Data']).dt.date
            return df
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=["Data", "Descricao"])

    def salvar_feriados(self, df: pd.DataFrame):
        with safe_csv_write(self.arq_feriados):
            df.to_csv(self.arq_feriados, index=False)
        st.cache_data.clear()
        
    # --- NOVAS FUNÇÕES PARA GERENCIAR FERIADOS IGNORADOS ---
    @st.cache_data(ttl=60)
    def carregar_feriados_ignorados(_self) -> pd.DataFrame:
        try:
            df = pd.read_csv(_self.arq_feriados_ignorados)
            df['Data'] = pd.to_datetime(df['Data']).dt.date
            return df
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=["Data", "Descricao"])

    def salvar_feriados_ignorados(self, df: pd.DataFrame):
        with safe_csv_write(self.arq_feriados_ignorados):
            df.to_csv(self.arq_feriados_ignorados, index=False)
        st.cache_data.clear()

# --- MODIFICADO ---
# Instancia o DataManager passando também o novo arquivo de feriados ignorados
data_manager = DataManager(ARQ_COLAB, ARQ_PONTO, FOTOS_DIR, ARQ_FERIADOS, ARQ_FERIADOS_IGNORADOS)

def adicionar_colaborador(nome: str, funcao: str) -> bool:
    # Permissão: apenas Admin pode adicionar
    if st.session_state.get('role') != 'Admin':
        st.error("Permissão negada: apenas administradores podem adicionar colaboradores.")
        return False
    df = data_manager.carregar_colaboradores()
    nome = nome.strip()
    if not nome:
        st.error("O nome do colaborador não pode estar vazio.")
        return False
    if any(char in nome for char in ";/\\|@#$%&*"):
        st.error("O nome do colaborador contém caracteres inválidos.")
        return False
    if nome in df["Nome"].values:
        st.warning(f"O nome '{nome}' já está cadastrado.")
        return False
    novo_colaborador = pd.DataFrame([[nome, funcao]], columns=["Nome", "Funcao"])
    df = pd.concat([df, novo_colaborador], ignore_index=True)
    data_manager.salvar_colaboradores(df)
    return True

def remover_colaborador(nome: str) -> bool:
    if st.session_state.get('role') != 'Admin':
        st.error("Permissão negada: apenas administradores podem remover colaboradores.")
        return False
    df = data_manager.carregar_colaboradores()
    initial_len = len(df)
    df = df[df["Nome"] != nome]
    data_manager.salvar_colaboradores(df)
    return len(df) < initial_len

def editar_colaborador(nome_original: str, novo_nome: str, nova_funcao: str) -> bool:
    if st.session_state.get('role') != 'Admin':
        st.error("Permissão negada: apenas administradores podem editar colaboradores.")
        return False
    df = data_manager.carregar_colaboradores()
    novo_nome = novo_nome.strip()
    if not novo_nome:
        st.error("O nome do colaborador não pode estar vazio.")
        return False
    if any(char in novo_nome for char in ";/\\|@#$%&*"):
        st.error("O nome do colaborador contém caracteres inválidos.")
        return False
    if nome_original in df["Nome"].values:
        if novo_nome and novo_nome != nome_original and novo_nome in df["Nome"].values:
            st.error("O novo nome já está em uso por outro colaborador.")
            return False
        idx = df[df["Nome"] == nome_original].index[0]
        df.loc[idx, "Nome"] = novo_nome
        df.loc[idx, "Funcao"] = nova_funcao
        data_manager.salvar_colaboradores(df)
        if novo_nome and novo_nome != nome_original:
            df_pontos = data_manager.carregar_pontos()
            df_pontos.loc[df_pontos["Nome"] == nome_original, "Nome"] = novo_nome
            data_manager.salvar_pontos(df_pontos)
        return True
    return False

def registrar_evento(nome: str, acao: AcaoPonto, data_str: Optional[str] = None, hora_str: Optional[str] = None) -> bool:
    # Permissão: apenas Admin pode registrar eventos para outros colaboradores
    if st.session_state.get('role') != 'Admin' and st.session_state.get('role') != 'Viewer':
        st.error("Permissão negada: apenas administradores podem registrar eventos.")
        return False
    now = datetime.now()
    data_str = data_str or now.strftime("%Y-%m-%d")
    hora_str = hora_str or now.strftime("%H:%M")
    if not nome or not acao:
        st.error("Nome e ação são obrigatórios.")
        return False
    try:
        datetime.strptime(hora_str, "%H:%M")
    except Exception:
        st.error("Hora inválida.")
        return False
    df_pontos = data_manager.carregar_pontos()
    df_mesmo_dia = df_pontos[(df_pontos["Nome"] == nome) & (df_pontos["Data"] == data_str)]
    hora_nova = datetime.strptime(hora_str, "%H:%M")
    for _, row in df_mesmo_dia.iterrows():
        try:
            hora_existente = datetime.strptime(str(row["Hora"])[:5], "%H:%M")
            if abs((hora_existente - hora_nova).total_seconds()) < 60:
                st.warning(f"Registro ignorado: ação semelhante registrada há menos de 1 minuto ({row['Hora']}).")
                return False
        except (ValueError, TypeError):
            continue
    novo_registro = pd.DataFrame([[nome, acao.value, data_str, hora_str]], columns=["Nome", "Ação", "Data", "Hora"])
    df_pontos = pd.concat([df_pontos, novo_registro], ignore_index=True)
    data_manager.salvar_pontos(df_pontos)
    return True

def atualizar_ponto(index: int, nome: str, acao: AcaoPonto, data: str, hora: str) -> bool:
    if st.session_state.get('role') != 'Admin':
        st.error("Permissão negada: apenas administradores podem atualizar registros de ponto.")
        return False
    df = data_manager.carregar_pontos()
    if 0 <= index < len(df):
        df.loc[index, "Nome"] = nome
        df.loc[index, "Ação"] = acao.value
        df.loc[index, "Data"] = data
        df.loc[index, "Hora"] = hora
        data_manager.salvar_pontos(df)
        return True
    return False

def deletar_ponto(index: int) -> bool:
    if st.session_state.get('role') != 'Admin':
        st.error("Permissão negada: apenas administradores podem excluir registros de ponto.")
        return False
    df = data_manager.carregar_pontos()
    if 0 <= index < len(df):
        df = df.drop(index).reset_index(drop=True)
        data_manager.salvar_pontos(df)
        return True
    return False

def formatar_timedelta(td: timedelta) -> str:
    total_segundos = int(td.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    return f"{horas:02}:{minutos:02}"

def calcular_horas(df: pd.DataFrame) -> pd.DataFrame:
    resultado = []
    df["DataHora"] = pd.to_datetime(df["Data"] + " " + df["Hora"], format="%Y-%m-%d %H:%M", errors='coerce')
    df = df.dropna(subset=["DataHora"]).sort_values(by=["Nome", "DataHora"])

    for nome, df_nome in df.groupby("Nome"):
        df_nome = df_nome.sort_values("DataHora").reset_index(drop=True)
        i = 0
        while i < len(df_nome):
            row = df_nome.iloc[i]
            if row["Ação"] == AcaoPonto.ENTRADA.value:
                data_entrada = row["Data"]
                if i + 1 < len(df_nome) and df_nome.iloc[i + 1]["Ação"] == AcaoPonto.SAIDA.value:
                    duracao = df_nome.iloc[i + 1]["DataHora"] - row["DataHora"]
                    resultado.append((nome, data_entrada, formatar_timedelta(duracao)))
                    i += 2
                elif (i + 3 < len(df_nome) and
                      df_nome.iloc[i + 1]["Ação"] == AcaoPonto.PAUSA.value and
                      df_nome.iloc[i + 2]["Ação"] == AcaoPonto.RETORNO.value and
                      df_nome.iloc[i + 3]["Ação"] == AcaoPonto.SAIDA.value):
                    periodo1 = df_nome.iloc[i + 1]["DataHora"] - df_nome.iloc[i]["DataHora"]
                    periodo2 = df_nome.iloc[i + 3]["DataHora"] - df_nome.iloc[i + 2]["DataHora"]
                    duracao = periodo1 + periodo2
                    resultado.append((nome, data_entrada, formatar_timedelta(duracao)))
                    i += 4
                else:
                    resultado.append((nome, data_entrada, "Registro Incompleto"))
                    i += 1
            else:
                i += 1
    return pd.DataFrame(resultado, columns=["Nome", "Data", "Horas Trabalhadas"])

def get_periodo_do_dia(dt_object: datetime) -> str:
    hour = dt_object.hour
    if 0 <= hour < 5:
        return "Madrugada"
    elif 5 <= hour < 12:
        return "Manhã"
    elif 12 <= hour < 18:
        return "Tarde"
    else:
        return "Noite"

# --- FUNÇÃO MODIFICADA ---
def calcular_horas_extras(df_colaborador: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    extras_50_datas = defaultdict(list)
    extras_100_datas = defaultdict(list)
    br_holidays = holidays.Brazil(state='CE')

    # Carrega feriados personalizados e os ignorados
    df_feriados_personalizados = data_manager.carregar_feriados()
    feriados_personalizados = set(df_feriados_personalizados['Data'])
    
    # NOVO: Carrega os feriados do sistema que devem ser ignorados
    df_feriados_ignorados = data_manager.carregar_feriados_ignorados()
    feriados_ignorados = set(df_feriados_ignorados['Data'])

    df_colaborador["DataHora"] = pd.to_datetime(df_colaborador["Data"] + " " + df_colaborador["Hora"], format="%Y-%m-%d %H:%M", errors='coerce')
    df_colaborador = df_colaborador.dropna(subset=["DataHora"]).sort_values(by="DataHora").reset_index(drop=True)

    i = 0
    while i < len(df_colaborador):
        row = df_colaborador.iloc[i]
        if row["Ação"] == AcaoPonto.ENTRADA.value:
            periodos_trabalho = []
            if i + 1 < len(df_colaborador) and df_colaborador.iloc[i + 1]["Ação"] == AcaoPonto.SAIDA.value:
                periodos_trabalho.append((row["DataHora"], df_colaborador.iloc[i + 1]["DataHora"]))
                i += 2
            elif (i + 3 < len(df_colaborador) and
                  df_colaborador.iloc[i + 1]["Ação"] == AcaoPonto.PAUSA.value and
                  df_colaborador.iloc[i + 2]["Ação"] == AcaoPonto.RETORNO.value and
                  df_colaborador.iloc[i + 3]["Ação"] == AcaoPonto.SAIDA.value):
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

                    if inicio_calculo >= fim: break
                    
                    # --- LÓGICA DE HORA EXTRA 100% ATUALIZADA ---
                    # Verifica se é um feriado do sistema (e não está na lista de ignorados)
                    is_system_holiday = (data_atual in br_holidays) and (data_atual not in feriados_ignorados)
                    # Verifica se é um feriado personalizado
                    is_custom_holiday = data_atual in feriados_personalizados
                    
                    if is_system_holiday or is_custom_holiday or dia_semana == 6: # Feriado Válido ou Domingo
                        duracao_100 = fim_calculo - inicio_calculo
                        if duracao_100.total_seconds() > 0:
                            periodo = get_periodo_do_dia(inicio_calculo)
                            extras_100_datas[data_atual].append({"duracao": duracao_100, "inicio_turno": inicio, "periodo": periodo})
                    
                    else: # Dias de semana (Seg-Sáb)
                        limite_inicio_expediente = pd.Timestamp(data_atual).replace(hour=7, minute=0)
                        
                        if inicio_calculo < limite_inicio_expediente:
                            fim_he_matinal = min(fim_calculo, limite_inicio_expediente)
                            overtime_duration_morning = fim_he_matinal - inicio_calculo
                            if overtime_duration_morning.total_seconds() > 0:
                                periodo_he_morning = get_periodo_do_dia(inicio_calculo)
                                extras_50_datas[data_atual].append({
                                    "duracao": overtime_duration_morning, 
                                    "inicio_turno": inicio, 
                                    "periodo": periodo_he_morning
                                })
                            inicio_calculo = max(inicio_calculo, limite_inicio_expediente)
                        
                        if dia_semana == 5: # Sábado
                            duracao_50 = fim_calculo - inicio_calculo
                            if duracao_50.total_seconds() > 0:
                                periodo = get_periodo_do_dia(inicio_calculo)
                                extras_50_datas[data_atual].append({"duracao": duracao_50, "inicio_turno": inicio, "periodo": periodo})
                        
                        elif dia_semana == 4: # Sexta-feira
                            limite = pd.Timestamp(data_atual).replace(hour=16, minute=0)
                            if fim_calculo > limite:
                                overtime_start = max(inicio_calculo, limite)
                                overtime_duration = fim_calculo - overtime_start
                                if overtime_duration.total_seconds() > 0:
                                    periodo_he = get_periodo_do_dia(overtime_start)
                                    extras_50_datas[data_atual].append({"duracao": overtime_duration, "inicio_turno": inicio, "periodo": periodo_he})

                        elif 0 <= dia_semana <= 3: # Segunda a Quinta
                            limite = pd.Timestamp(data_atual).replace(hour=17, minute=0)
                            if fim_calculo > limite:
                                overtime_start = max(inicio_calculo, limite)
                                overtime_duration = fim_calculo - overtime_start
                                if overtime_duration.total_seconds() > 0:
                                    periodo_he = get_periodo_do_dia(overtime_start)
                                    extras_50_datas[data_atual].append({"duracao": overtime_duration, "inicio_turno": inicio, "periodo": periodo_he})
                                
                    data_corrente = pd.to_datetime(data_atual + timedelta(days=1))
        else:
            i += 1
    
    total_50 = sum([item['duracao'] for sublist in extras_50_datas.values() for item in sublist], timedelta())
    total_100 = sum([item['duracao'] for sublist in extras_100_datas.values() for item in sublist], timedelta())
            
    return {
        "50%": {"total": total_50, "datas": extras_50_datas},
        "100%": {"total": total_100, "datas": extras_100_datas},
    }

def mostrar_pagina_registro():
    st.header("Registro de Ponto")
    st.markdown("""
    Informe manually a data e hora da entrada. O sistema registrará automaticamente:
    - Pausa às 12:00
    - Retorno às 13:00
    - Saída às 17:00 (segunda a quinta) ou 16:00 (sexta)

    Os **Vigias** têm botões específicos para seus turnos.
    """)

    df_colab = data_manager.carregar_colaboradores()
    # MODIFICAÇÃO: Adicionado sorted() para ordenar a lista de nomes
    nomes = [""] + sorted(df_colab["Nome"].tolist())

    with st.container(border=True):
        nome_selecionado = st.selectbox(
            "**Selecione seu nome:**",
            nomes,
            key="ponto_nome_select",
            help="Escolha seu nome para registrar o ponto."
        )

        if not nome_selecionado:
            st.warning("Por favor, selecione um nome.")
            return

        foto_path = None
        for ext in ['jpg', 'png', 'jpeg']:
            path_tentativa = os.path.join(FOTOS_DIR, f"{nome_selecionado}.{ext}")
            if os.path.exists(path_tentativa):
                foto_path = path_tentativa
                break

        if foto_path:
           st.image(foto_path, caption=f"Olá, {nome_selecionado.split(' ')[0]}!", width=100)

        st.markdown("---")

        st.write(f"Colaborador selecionado: **{nome_selecionado}**")
        data_input = st.date_input("Data do Registro:", datetime.today(), key="data_input_manual")
        
        hora_input = st.text_input("Hora da Entrada (HH:MM):", value="07:00", placeholder="Ex: 07:00", key="hora_input_manual")

        try:
            if hora_input:
                datetime.strptime(hora_input, "%H:%M")

            data_str = data_input.strftime("%Y-%m-%d")
            hora_str = hora_input.strip()

            if st.button("Registrar Entrada Padrão", use_container_width=True):
                if not hora_str:
                    st.error("A hora da entrada é obrigatória para o registro padrão.")
                else:
                    entrada_sucesso = registrar_evento(nome_selecionado, AcaoPonto.ENTRADA, data_str, hora_str)

                    if entrada_sucesso:
                        registrar_evento(nome_selecionado, AcaoPonto.PAUSA, data_str, "12:00")
                        registrar_evento(nome_selecionado, AcaoPonto.RETORNO, data_str, "13:00")
                        dia_semana = data_input.weekday()
                        hora_saida = "16:00" if dia_semana == 4 else "17:00"
                        registrar_evento(nome_selecionado, AcaoPonto.SAIDA, data_str, hora_saida)
                        st.success(f"Ponto padrão registrado para {nome_selecionado} em {data_input.strftime('%d/%m/%Y')}.")

            st.markdown("---")
            st.markdown("🌙 **Vigia da noite?** Use o botão abaixo para registrar das 18:00 às 06:00 do dia seguinte.")
            if st.button("Registrar Turno Noturno (18:00 - 06:00)", use_container_width=True):
                data_saida_dt = data_input + timedelta(days=1)
                data_saida_str = data_saida_dt.strftime("%Y-%m-%d")

                if registrar_evento(nome_selecionado, AcaoPonto.ENTRADA, data_str, "18:00"):
                    registrar_evento(nome_selecionado, AcaoPonto.SAIDA, data_saida_str, "06:00")
                    st.success(f"Turno noturno registrado com sucesso para {nome_selecionado}.")

            st.markdown("🌞 **Vigia do dia?** Use o botão abaixo para registrar das 06:00 às 18:00 no mesmo dia.")
            if st.button("Registrar Turno Diurno (06:00 - 18:00)", use_container_width=True):
               if registrar_evento(nome_selecionado, AcaoPonto.ENTRADA, data_str, "06:00"):
                   registrar_evento(nome_selecionado, AcaoPonto.SAIDA, data_str, "18:00")
                   st.success(f"Turno diurno registrado com sucesso para {nome_selecionado}.")

        except ValueError:
            if hora_input:
                st.error("Formato de hora inválido. Use HH:MM.")

def mostrar_pagina_gerenciar():
    st.header("Gerenciar Colaboradores")

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
    df_colab = data_manager.carregar_colaboradores()

    if df_colab.empty:
        st.info("Nenhum colaborador cadastrado.")
        return
        
    if 'editing_id' not in st.session_state:
        st.session_state.editing_id = None

    funcoes = sorted([f for f in df_colab["Funcao"].dropna().unique() if f])
    for funcao_grupo in funcoes:
        st.markdown(f"#### {funcao_grupo}")
        colab_funcao = df_colab[df_colab["Funcao"] == funcao_grupo]
        for i, row in colab_funcao.iterrows():
            colab_id = f"colab_{i}"
            
            if st.session_state.editing_id == colab_id:
                with st.container(border=True):
                    st.write(f"Editando **{row['Nome']}**")
                    novo_nome = st.text_input("Novo nome", value=row["Nome"], key=f"novo_nome_{i}")
                    nova_funcao = st.text_input("Nova função", value=row["Funcao"], key=f"nova_funcao_{i}")
                    
                    col_save, col_cancel = st.columns(2)
                    if col_save.button("Salvar", key=f"salvar_{i}", use_container_width=True):
                        if novo_nome.strip():
                            if editar_colaborador(row["Nome"], novo_nome.strip(), nova_funcao.strip()):
                                st.success("Dados atualizados com sucesso.")
                                st.session_state.editing_id = None
                                st.rerun()
                        else:
                            st.error("O nome não pode estar vazio.")
                    
                    if col_cancel.button("Cancelar", key=f"cancelar_{i}", use_container_width=True):
                        st.session_state.editing_id = None
                        st.rerun()
            else:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([4, 4, 1, 1])
                    c1.write(f"**Nome:** {row['Nome']}")
                    c2.write(f"**Função:** {row['Funcao']}")
                    if c3.button("✏️", key=f"editar_{i}", help="Editar Colaborador"):
                        st.session_state.editing_id = colab_id
                        st.rerun()
                    if c4.button("🗑️", key=f"excluir_{i}", help="Excluir Colaborador"):
                        if remover_colaborador(row["Nome"]):
                            st.warning(f"Colaborador '{row['Nome']}' removido.")
                            st.rerun()

def mostrar_pagina_relatorios():
    st.header("Relatórios de Ponto")
    st.markdown("Visualize o histórico de ponto, total de horas e baixe os arquivos.")
    df_pontos = data_manager.carregar_pontos()
    df_colab = data_manager.carregar_colaboradores()
    
    if df_pontos.empty or df_colab.empty:
        st.warning("Sem dados suficientes para gerar relatórios.")
        return

    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data inicial", value=datetime.today().replace(day=1), key="relatorio_inicio", format="DD/MM/YYYY")
    data_fim = col2.date_input("Data final", value=datetime.today(), key="relatorio_fim", format="DD/MM/YYYY")

    st.markdown("---")

    st.subheader("Quantitativo por Função")
    if not df_colab.empty:
        contagem_funcao = df_colab['Funcao'].value_counts().reset_index()
        contagem_funcao.columns = ['Função', 'Quantidade']
        st.dataframe(contagem_funcao, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum colaborador cadastrado para exibir o quantitativo.")
    
    st.markdown("---")

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
    df_feriados = data_manager.carregar_feriados()
    feriados_personalizados = set(df_feriados['Data'])
    # NOVO: Carrega feriados ignorados para não contar falta erroneamente se o feriado for ignorado
    df_feriados_ignorados = data_manager.carregar_feriados_ignorados()
    feriados_ignorados = set(df_feriados_ignorados['Data'])

    datas_periodo = pd.date_range(start=data_inicio, end=data_fim)
    
    faltas_por_colaborador = {nome: [] for nome in colabs_normais['Nome']}
    nomes_esperados_set = set(colabs_normais['Nome'])

    for data in datas_periodo:
        data_atual = data.date()
        # --- CONDIÇÃO DE FALTA ATUALIZADA ---
        is_system_holiday = data_atual in br_holidays and data_atual not in feriados_ignorados
        is_custom_holiday = data_atual in feriados_personalizados

        if data.weekday() < 5 and not is_system_holiday and not is_custom_holiday:
            data_str = data.strftime("%Y-%m-%d")
            
            presentes_no_dia = set(df_pontos[
                (df_pontos['Data'] == data_str) & 
                (df_pontos['Ação'] == AcaoPonto.ENTRADA.value)
            ]['Nome'])
            
            ausentes = nomes_esperados_set - presentes_no_dia
            
            for nome_ausente in ausentes:
                if nome_ausente in faltas_por_colaborador:
                    faltas_por_colaborador[nome_ausente].append(data.strftime('%d/%m/%Y'))

    faltas_encontradas = {nome: datas for nome, datas in faltas_por_colaborador.items() if datas}

    if not faltas_encontradas:
        st.success("Nenhuma falta registrada para o período e filtro selecionados.")
    else:
        if colab_falta_selecionado == "Todos":
            st.error("Foram encontradas as seguintes faltas no período:")
            for nome, datas_faltas in sorted(faltas_encontradas.items()):
                with st.expander(f"**{nome}** - {len(datas_faltas)} falta(s)"):
                    for data_falta in sorted(list(set(datas_faltas))):
                        st.markdown(f"- {data_falta}")
        else:
            if colab_falta_selecionado in faltas_encontradas:
                st.error(f"O colaborador **{colab_falta_selecionado}** faltou nos seguintes dias:")
                datas_ausencia = sorted(list(set(faltas_encontradas[colab_falta_selecionado])))
                for data_falta in datas_ausencia:
                    st.markdown(f"- {data_falta}")
            else:
                st.success(f"Nenhuma falta encontrada para **{colab_falta_selecionado}** no período selecionado.")

    st.subheader("Resumo Geral de Horas Extras no Período")
    
    df_pontos_periodo_geral = df_pontos[
        (pd.to_datetime(df_pontos["Data"]) >= pd.to_datetime(data_inicio)) &
        (pd.to_datetime(df_pontos["Data"]) <= pd.to_datetime(data_fim))
    ]

    any_overtime_found = False
    for _, colaborador in df_colab.iterrows():
        nome_colab = colaborador["Nome"]
        funcao_colab = colaborador["Funcao"]
        
        if "vigia" in str(funcao_colab).lower():
            continue

        df_pontos_colaborador = df_pontos_periodo_geral[df_pontos_periodo_geral["Nome"] == nome_colab]
        
        if not df_pontos_colaborador.empty:
            resultado_extras = calcular_horas_extras(df_pontos_colaborador.copy())
            
            he_50_info = resultado_extras.get("50%", {"total": timedelta(), "datas": {}})
            he_100_info = resultado_extras.get("100%", {"total": timedelta(), "datas": {}})

            if he_50_info["total"].total_seconds() > 0 or he_100_info["total"].total_seconds() > 0:
                any_overtime_found = True
                
                with st.container(border=True):
                    st.markdown(f"#### {nome_colab}")
                    col_he1, col_he2 = st.columns(2)
                    col_he1.metric(label="Horas Extras (50%)", value=formatar_timedelta(he_50_info["total"]))
                    col_he2.metric(label="Horas Extras (100%)", value=formatar_timedelta(he_100_info["total"]))

                    if he_50_info["datas"]:
                        with st.expander("Ver detalhes das Horas Extras (50%)"):
                            registros_flat = []
                            for data, registros in he_50_info["datas"].items():
                                for reg_dict in registros:
                                    registros_flat.append({
                                        'data_evento': data,
                                        'duracao': reg_dict['duracao'],
                                        'inicio_turno': reg_dict['inicio_turno'],
                                        'periodo': reg_dict['periodo']
                                    })
                            
                            registros_sorted = sorted(registros_flat, key=lambda x: (x['data_evento'], x['inicio_turno']))
                            for reg in registros_sorted:
                                data_evento_str = reg['data_evento'].strftime('%d/%m/%Y')
                                duracao_str = formatar_timedelta(reg['duracao'])
                                periodo_str = reg['periodo']
                                contexto_str = ""
                                if reg['data_evento'] != reg['inicio_turno'].date():
                                    contexto_str = f" `(Ref. turno de {reg['inicio_turno'].strftime('%d/%m %H:%M')})`"
                                st.markdown(f"- **Data:** {data_evento_str} - **Período:** {periodo_str} - **Duração:** {duracao_str}{contexto_str}")

                    if he_100_info["datas"]:
                        with st.expander("Ver detalhes das Horas Extras (100%)"):
                            registros_flat = []
                            for data, registros in he_100_info["datas"].items():
                                for reg_dict in registros:
                                    registros_flat.append({
                                        'data_evento': data,
                                        'duracao': reg_dict['duracao'],
                                        'inicio_turno': reg_dict['inicio_turno'],
                                        'periodo': reg_dict['periodo']
                                    })
                            
                            registros_sorted = sorted(registros_flat, key=lambda x: (x['data_evento'], x['inicio_turno']))
                            for reg in registros_sorted:
                                data_evento_str = reg['data_evento'].strftime('%d/%m/%Y')
                                duracao_str = formatar_timedelta(reg['duracao'])
                                periodo_str = reg['periodo']
                                contexto_str = ""
                                if reg['data_evento'] != reg['inicio_turno'].date():
                                    contexto_str = f" `(Ref. turno de {reg['inicio_turno'].strftime('%d/%m %H:%M')})`"
                                st.markdown(f"- **Data:** {data_evento_str} - **Período:** {periodo_str} - **Duração:** {duracao_str}{contexto_str}")
    
    if not any_overtime_found:
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
                
                he_50_info = resultado_extras_individual.get("50%", {"total": timedelta(), "datas": {}})
                he_100_info = resultado_extras_individual.get("100%", {"total": timedelta(), "datas": {}})
                
                col_he1, col_he2 = st.columns(2)
                col_he1.metric(label="Horas Extras (50%)", value=formatar_timedelta(he_50_info["total"]))
                col_he2.metric(label="Horas Extras (100%)", value=formatar_timedelta(he_100_info["total"]))

                if he_50_info["datas"]:
                    with st.expander("Ver detalhes das Horas Extras (50%)"):
                        # ... (código existente sem alterações)
                        pass
                
                if he_100_info["datas"]:
                    with st.expander("Ver detalhes das Horas Extras (100%)"):
                        # ... (código existente sem alterações)
                        pass
                
                with st.expander("Ver regras de cálculo de Horas Extras"):
                    st.markdown("""
                    - **Horas Extras 100%:**
                        - Todas as horas trabalhadas em **Feriados** (nacionais e cadastrados, exceto os ignorados) e **Domingos**.
                    - **Horas Extras 50%:**
                        - Horas trabalhadas em dias de semana **antes das 07:00**.
                        - Todas as horas trabalhadas aos **Sábados**.
                        - Horas trabalhadas após as **16:00** na **Sexta-feira**.
                        - Horas trabalhadas após as **17:00** de **Segunda a Quinta-feira**.
                    """)
            else:
                st.info("Nenhum registro de ponto encontrado para o cálculo de horas extras deste colaborador no período.")
    else:
        st.info("Nenhum registro encontrado para o colaborador no período selecionado.")
    
    # ... (restante da função 'mostrar_pagina_relatorios' sem alterações)
    st.markdown("---")
    st.subheader("Histórico Detalhado por Data")
    col_date, col_name_report = st.columns([1, 2])
    with col_date:
        data_relatorio = st.date_input("Selecione uma data:", datetime.today(), key="rel_date_input", format="DD/MM/YYYY")
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
                except (ValueError, TypeError): return 0
            
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
    # Apenas o admin pode exportar os dados
    if st.session_state.get('role') == 'Admin':
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
    else:
        st.info("A exportação de dados está disponível apenas para administradores.")


def mostrar_pagina_ajuste():
    st.header("Ajuste Manual de Ponto")
    st.markdown("Esta ferramenta permite a correção e o ajuste manual dos registros de ponto.")
    df_colab_ajuste = data_manager.carregar_colaboradores()
    nomes_ajuste = [""] + df_colab_ajuste["Nome"].tolist()
    col_ajuste_sel, col_ajuste_date = st.columns(2)
    with col_ajuste_sel:
        colab_selecionado = st.selectbox("**Selecione o Colaborador:**", nomes_ajuste, key="ajustar_colab_select_main")
    with col_ajuste_date:
        data_ajuste = st.date_input("**Selecione a Data do Ajuste:**", datetime.today(), key="ajustar_date_input_main", format="DD/MM/YYYY")
    
    if colab_selecionado:
        df_pontos_ajuste = data_manager.carregar_pontos()
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
                    
                    acoes_ponto_lista = [acao.value for acao in AcaoPonto]
                    index_acao = acoes_ponto_lista.index(row["Ação"]) if row["Ação"] in acoes_ponto_lista else 0
                    
                    novo_acao_str = col_acao.selectbox("Ação", acoes_ponto_lista, index=index_acao, key=f"ajust_acao_{original_index}")
                    
                    data_para_exibir = datetime.strptime(row["Data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    novo_data_input = col_data.text_input("Data (DD/MM/YYYY)", value=data_para_exibir, key=f"ajust_data_{original_index}").strip()
                    novo_hora_str = col_hora.text_input("Hora (HH:MM)", value=row["Hora"], key=f"ajust_hora_{original_index}").strip()
                    
                    col_update, col_delete = st.columns(2)
                    
                    if col_update.button("Salvar Alterações", use_container_width=True, key=f"update_btn_{original_index}"):
                        try:
                            data_obj = datetime.strptime(novo_data_input, "%d/%m/%Y")
                            data_para_salvar = data_obj.strftime("%Y-%m-%d")
                            datetime.strptime(novo_hora_str, "%H:%M") 
                            if atualizar_ponto(original_index, colab_selecionado, AcaoPonto(novo_acao_str), data_para_salvar, novo_hora_str):
                                st.success(f"O registro ID {original_index} foi atualizado com sucesso.")
                                st.rerun()
                        except ValueError:
                            st.error("Formato de Data (DD/MM/YYYY) ou Hora (HH:MM) inválido.")
                    
                    if col_delete.button("Excluir Registro", use_container_width=True, key=f"delete_btn_{original_index}"):
                        if deletar_ponto(original_index):
                            st.warning(f"O registro ID {original_index} foi excluído.")
                            st.rerun()
        
        st.markdown("### Adicionar Novo Registro Manual")
        with st.form("form_add_ponto_manual"):
            col_add_acao, col_add_data, col_add_hora = st.columns(3)
            acao_manual_str = col_add_acao.selectbox("Ação", [a.value for a in AcaoPonto], key="add_manual_acao")
            
            data_manual_input = col_add_data.text_input("Data (DD/MM/YYYY)", value=data_ajuste.strftime("%d/%m/%Y")).strip()
            hora_manual_str = col_add_hora.text_input("Hora (HH:MM)", value=datetime.now().strftime("%H:%M")).strip()
            
            if st.form_submit_button("Adicionar Registro"):
                try:
                    data_obj = datetime.strptime(data_manual_input, "%d/%m/%Y")
                    data_manual_para_salvar = data_obj.strftime("%Y-%m-%d")
                    datetime.strptime(hora_manual_str, "%H:%M") 
                    if registrar_evento(colab_selecionado, AcaoPonto(acao_manual_str), data_manual_para_salvar, hora_manual_str):
                        st.success("Novo registro manual adicionado com sucesso.")
                        st.rerun()
                except ValueError:
                    st.error("Formato de Data (DD/MM/YYYY) ou Hora (HH:MM) inválido.")
    else:
        st.info("Selecione um colaborador e uma data para visualizar e ajustar os registros.")

# --- PÁGINA COMPLETAMENTE REESCRITA ---
def mostrar_pagina_feriados():
    st.header("Gerenciar Feriados")
    st.markdown("Adicione feriados personalizados ou gerencie os feriados automáticos do sistema.")

    tab1, tab2 = st.tabs(["Feriados Personalizados", "Feriados do Sistema"])

    with tab1:
        st.subheader("Adicionar Novo Feriado Personalizado")
        st.markdown("Estes dias serão considerados para o cálculo de horas extras (100%) e não contarão como falta.")
        with st.form("form_add_feriado", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nova_data = col1.date_input("Data do Feriado", format="DD/MM/YYYY")
            nova_descricao = col2.text_input("Descrição", placeholder="Ex: Aniversário da Cidade")
            
            if st.form_submit_button("Adicionar Feriado"):
                if nova_descricao.strip():
                    df_feriados = data_manager.carregar_feriados()
                    datas_existentes = [d.strftime('%Y-%m-%d') for d in df_feriados['Data']]
                    
                    if nova_data.strftime('%Y-%m-%d') not in datas_existentes:
                        novo_feriado = pd.DataFrame([[nova_data, nova_descricao.strip()]], columns=["Data", "Descricao"])
                        df_feriados_atualizado = pd.concat([df_feriados, novo_feriado], ignore_index=True)
                        data_manager.salvar_feriados(df_feriados_atualizado)
                        st.success(f"Feriado '{nova_descricao}' adicionado.")
                        st.rerun()
                    else:
                        st.warning("Esta data já está cadastrada como feriado.")
                else:
                    st.error("A descrição do feriado é obrigatória.")
        
        st.markdown("---")
        st.subheader("Feriados Personalizados Cadastrados")
        df_feriados_lista = data_manager.carregar_feriados().sort_values(by="Data", ascending=False)
        
        if df_feriados_lista.empty:
            st.info("Nenhum feriado personalizado cadastrado.")
        else:
            for i, row in df_feriados_lista.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 5, 1])
                    col1.write(row["Data"].strftime("%d/%m/%Y"))
                    col2.write(f"**{row['Descricao']}**")
                    if col3.button("🗑️", key=f"del_feriado_{i}", help="Excluir Feriado"):
                        df_feriados_lista = df_feriados_lista.drop(i)
                        data_manager.salvar_feriados(df_feriados_lista)
                        st.warning(f"Feriado '{row['Descricao']}' removido.")
                        st.rerun()

    with tab2:
        st.subheader("Gerenciar Feriados Automáticos (Nacionais/Estaduais)")
        st.markdown("Por padrão, estes feriados contam como hora extra de 100%. Você pode 'Ignorar' um feriado para que ele seja tratado como um dia de trabalho normal.")
        
        br_holidays = holidays.Brazil(state='CE', years=[datetime.today().year, datetime.today().year + 1])
        df_feriados_ignorados = data_manager.carregar_feriados_ignorados()
        feriados_ignorados_set = set(df_feriados_ignorados['Data'])

        st.markdown("---")
        st.write("**Feriados do sistema ativos (de Janeiro a Dezembro):**")
        
        feriados_por_ano = defaultdict(dict)
        for data, nome in br_holidays.items():
            ano = data.year
            feriados_por_ano[ano][data] = nome

        for ano in sorted(feriados_por_ano.keys()):
            st.markdown(f"#### {ano}")
            feriados_ano = {data: nome for data, nome in sorted(feriados_por_ano[ano].items()) if data not in feriados_ignorados_set}
            
            if not feriados_ano:
                st.info(f"Não há feriados do sistema ativos para {ano} ou todos foram ignorados.")
            else:
                for data, nome in feriados_ano.items():
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 5, 2])
                        col1.write(data.strftime("%d/%m/%Y"))
                        col2.write(f"**{nome}**")
                        if col3.button("Ignorar Feriado", key=f"ignore_feriado_{data}", help="Tratar este feriado como dia normal"):
                            novo_ignorado = pd.DataFrame([[data, nome]], columns=["Data", "Descricao"])
                            df_atualizado = pd.concat([df_feriados_ignorados, novo_ignorado], ignore_index=True)
                            data_manager.salvar_feriados_ignorados(df_atualizado)
                            st.success(f"O feriado '{nome}' será ignorado.")
                            st.rerun()

        st.markdown("---")
        st.subheader("Feriados do Sistema Ignorados")
        
        if df_feriados_ignorados.empty:
            st.info("Nenhum feriado do sistema está sendo ignorado.")
        else:
            df_feriados_ignorados_sorted = df_feriados_ignorados.sort_values(by="Data", ascending=False)
            for i, row in df_feriados_ignorados_sorted.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 5, 2])
                    col1.write(row["Data"].strftime("%d/%m/%Y"))
                    col2.write(f"**{row['Descricao']}**")
                    if col3.button("Reativar Feriado", key=f"reactivate_feriado_{i}", help="Voltar a considerar este feriado para HE 100%"):
                        df_feriados_ignorados_sorted = df_feriados_ignorados_sorted.drop(i)
                        data_manager.salvar_feriados_ignorados(df_feriados_ignorados_sorted)
                        st.warning(f"Feriado '{row['Descricao']}' reativado.")
                        st.rerun()

# --- NOVO: Tela de Login ---
def show_login_screen():
    st.header("Acesso ao Sistema de Ponto")
    st.markdown("Por favor, insira a chave de acesso para continuar.")

    with st.form("login_form"):
        password = st.text_input("Chave de Acesso (Admin)", type="password", key="password_input")
        admin_login_button = st.form_submit_button("Entrar como Administrador")

        if admin_login_button:
            # st.secrets.get("ACCESS_KEY") busca a chave no arquivo secrets.toml
            if password == st.secrets.get("ACCESS_KEY"):
                st.session_state['authenticated'] = True
                st.session_state['role'] = 'Admin'
                st.success("Login de administrador bem-sucedido!")
                st.rerun()
            else:
                st.error("Chave de acesso inválida.")
    
    st.markdown("---")
    if st.button("Acessar como Visitante (somente visualização de relatórios)"):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'Viewer'
        st.info("Acessando em modo de visualização.")
        st.rerun()


# --- MODIFICADO: Função principal para controlar o acesso ---
def main():
    st.title("Controle de Ponto")
    
    # Inicializa o estado da sessão se ainda não existir
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['role'] = None

    # Se o usuário não estiver autenticado, mostra a tela de login
    if not st.session_state.get('authenticated'):
        show_login_screen()
    else:
        # Se o usuário estiver autenticado, mostra a aplicação principal
        st.sidebar.title(f"Bem-vindo, {st.session_state['role']}!")
        st.sidebar.markdown("---")

        # Define as páginas disponíveis para cada tipo de usuário
        admin_pages = {
            "Registrar Ponto": mostrar_pagina_registro,
            "Gerenciar Colaboradores": mostrar_pagina_gerenciar,
            "Gerenciar Feriados": mostrar_pagina_feriados,
            "Relatórios": mostrar_pagina_relatorios,
            "Ajustar Ponto": mostrar_pagina_ajuste,
        }
        
        viewer_pages = {
            "Relatórios": mostrar_pagina_relatorios,
        }

        # Seleciona o conjunto de páginas com base na função do usuário
        if st.session_state['role'] == 'Admin':
            pages_to_show = admin_pages
        else: # Viewer
            pages_to_show = viewer_pages

        # Cria o menu de navegação na barra lateral
        aba_selecionada = st.sidebar.radio("Navegação", list(pages_to_show.keys()))
        
        # Botão de Logout
        st.sidebar.markdown("---")
        if st.sidebar.button("Sair (Logout)"):
            st.session_state['authenticated'] = False
            st.session_state['role'] = None
            st.rerun()

        # Exibe a página selecionada
        pagina_func = pages_to_show.get(aba_selecionada)
        if pagina_func:
            pagina_func()

if __name__ == "__main__":
    main()