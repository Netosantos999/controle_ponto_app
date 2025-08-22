# Sistema de Controle de Ponto

Este é um sistema de controle de ponto desenvolvido em Python com a biblioteca Streamlit. A aplicação permite o registro de entradas e saídas de colaboradores, calcula o total de horas trabalhadas, horas extras (50% e 100%), e gera relatórios detalhados, com controle de acesso por nível de permissão.

## ✨ Funcionalidades

O sistema oferece uma interface web simples e intuitiva com as seguintes funcionalidades:

- **Controle de Acesso:**
  - **Tela de Login:** Protege o acesso ao sistema.
  - **Nível Administrador:** Acesso completo a todas as funcionalidades de gerenciamento e registro.
  - **Nível Visitante:** Acesso restrito apenas para visualização dos relatórios.

- **Registro de Ponto Simplificado:**
  - Registro de jornada padrão (ex: 07:00 às 17:00) com pausas automáticas.
  - Botões específicos para turnos de **Vigia** (diurno e noturno).
  - Exibição da foto do colaborador para fácil identificação.

- **Gerenciamento de Colaboradores (Admin):**
  - Adicionar, editar e remover colaboradores.
  - Associar colaboradores a diferentes funções (ex: "Pedreiro", "Vigia").

- **Gerenciamento de Feriados (Admin):**
  - **Feriados Personalizados:** Adicione feriados (ex: aniversários da cidade, pontos facultativos) que serão considerados para o cálculo de horas extras a 100%.
  - **Feriados do Sistema:** Visualize feriados nacionais/estaduais e opte por "ignorá-los", tratando-os como dias de trabalho normais.

- **Relatórios Detalhados:**
  - **Horas Trabalhadas:** Cálculo do total de horas trabalhadas por dia e por período.
  - **Horas Extras:** Cálculo automático de horas extras a 50% e 100%, considerando domingos e todos os feriados válidos (personalizados e do sistema).
  - **Relatório de Faltas:** Identificação de dias úteis sem registro de entrada.
  - **Resumo por Função:** Quantitativo de colaboradores por cargo.
  - Filtros por período e por colaborador.

- **Ajuste Manual de Ponto (Admin):**
  - Ferramenta administrativa para corrigir, adicionar ou excluir registros de ponto de qualquer colaborador.

- **Exportação de Dados (Admin):**
  - Possibilidade de baixar os registros de ponto e a lista de colaboradores em formato `.csv`.

## 🛠️ Tecnologias Utilizadas

- **Python:** Linguagem de programação principal.
- **Streamlit:** Framework para a criação da interface web.
- **Pandas:** Biblioteca para manipulação e análise dos dados.
- **Holidays:** Biblioteca para identificar feriados nacionais e estaduais.

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
    - No Windows: `.\venv\Scripts\activate`
    - No Linux/macOS: `source venv/bin/activate`

4.  **Instale as dependências:**
    O projeto contém um arquivo `requirements.txt` com todas as bibliotecas necessárias. Para instalá-las, execute:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Crie a chave de acesso do Administrador:**
    O sistema usa o gerenciador de segredos do Streamlit. Crie uma pasta `.streamlit` e, dentro dela, um arquivo chamado `secrets.toml`. Adicione o seguinte conteúdo ao arquivo:
    ```toml
    # .streamlit/secrets.toml
    ACCESS_KEY = "SUA_SENHA_SECRETA_AQUI"
    ```
    Substitua `"SUA_SENHA_SECRETA_AQUI"` pela senha que desejar para o login de administrador.

6.  **Execute a aplicação:**
    Após a instalação, inicie o servidor do Streamlit com o seguinte comando:
    ```bash
    streamlit run PONTOS.py
    ```

7.  **Acesse a aplicação:**
    Abra seu navegador e acesse o endereço fornecido pelo Streamlit (geralmente `http://localhost:8501`).

## 📂 Estrutura de Arquivos

- `PONTOS.py`: Arquivo principal que contém todo o código da aplicação.
- `requirements.txt`: Lista de dependências do Python.
- `.streamlit/secrets.toml`: Arquivo para armazenar a chave de acesso do administrador.
- `colaboradores.csv`: Banco de dados para armazenar os nomes e funções dos colaboradores.
- `registro_ponto.csv`: Banco de dados para armazenar todos os registros de ponto.
- `feriados.csv`: Banco de dados para feriados personalizados adicionados pelo usuário.
- `feriados_ignorados.csv`: Armazena os feriados do sistema que o usuário decidiu ignorar.
- `fotos_colaboradores/`: Diretório onde as fotos dos colaboradores devem ser armazenadas (o nome do arquivo de imagem deve ser idêntico ao nome do colaborador).
