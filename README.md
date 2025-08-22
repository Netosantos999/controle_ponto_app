# Sistema de Controle de Ponto

Este é um sistema de controle de ponto desenvolvido em Python com a biblioteca Streamlit. A aplicação permite o registro de entradas e saídas de colaboradores, calcula o total de horas trabalhadas, horas extras (50% e 100%), e gera relatórios detalhados.

## ✨ Funcionalidades

O sistema oferece uma interface web simples e intuitiva com as seguintes funcionalidades:

- **Registro de Ponto Simplificado:**
  - Registro de jornada padrão (ex: 07:00 às 17:00) com pausas automáticas.
  - Botões específicos para turnos de **Vigia** (diurno e noturno).
  - Exibição da foto do colaborador para fácil identificação.

- **Gerenciamento de Colaboradores:**
  - Adicionar, editar e remover colaboradores.
  - Associar colaboradores a diferentes funções (ex: "Pedreiro", "Vigia").

- **Relatórios Detalhados:**
  - **Horas Trabalhadas:** Cálculo do total de horas trabalhadas por dia e por período.
  - **Horas Extras:** Cálculo automático de horas extras a 50% (dias de semana e sábados) e 100% (domingos e feriados).
  - **Relatório de Faltas:** Identificação de dias úteis sem registro de entrada.
  - **Resumo por Função:** Quantitativo de colaboradores por cargo.
  - Filtros por período e por colaborador.

- **Ajuste Manual de Ponto:**
  - Ferramenta administrativa para corrigir, adicionar ou excluir registros de ponto de qualquer colaborador.

- **Exportação de Dados:**
  - Possibilidade de baixar os registros de ponto e a lista de colaboradores em formato `.csv`.

## 🛠️ Tecnologias Utilizadas

- **Python:** Linguagem de programação principal.
- **Streamlit:** Framework para a criação da interface web.
- **Pandas:** Biblioteca para manipulação e análise dos dados.
- **Holidays:** Biblioteca para identificar feriados nacionais e estaduais, garantindo a precisão no cálculo de horas extras.

## 🚀 Como Executar o Projeto

1.  **Pré-requisitos:**
    - Ter o Python 3.8 (ou superior) instalado.
    - Ter o `pip` (gerenciador de pacotes do Python) instalado.

2.  **Clone o repositório (se aplicável):**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

3.  **Crie um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    ```
    - No Windows:
      ```bash
      .\venv\Scripts\activate
      ```
    - No Linux/macOS:
      ```bash
      source venv/bin/activate
      ```

4.  **Instale as dependências:**
    O projeto contém um arquivo `requirements.txt` com todas as bibliotecas necessárias. Para instalá-las, execute:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute a aplicação:**
    Após a instalação, inicie o servidor do Streamlit com o seguinte comando:
    ```bash
    streamlit run PONTOS.py
    ```

6.  **Acesse a aplicação:**
    Abra seu navegador e acesse o endereço fornecido pelo Streamlit (geralmente `http://localhost:8501`).

## 📂 Estrutura de Arquivos

- `PONTOS.py`: Arquivo principal que contém todo o código da aplicação Streamlit.
- `requirements.txt`: Lista de dependências do Python.
- `colaboradores.csv`: Arquivo de banco de dados para armazenar os nomes e funções dos colaboradores.
- `registro_ponto.csv`: Arquivo de banco de dados para armazenar todos os registros de ponto.
- `fotos_colaboradores/`: Diretório onde as fotos dos colaboradores devem ser armazenadas (o nome do arquivo de imagem deve ser idêntico ao nome do colaborador).
