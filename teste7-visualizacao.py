import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Carregar dados
@st.cache_data
def carregar_dados():
    dados = pd.read_csv("dados_unidos_2024.zip", compression="zip")
    dados.drop(columns=['codigo_municipio_6', 'codigo_municipio_paciente', 'nome_padrao'], inplace=True)
    return dados



dados = carregar_dados()

# Dicionário para renomear as variáveis
nomes_amigaveis = {
    'ocorrencias_da_doenca': 'Total de Ocorrências',
    'ocorrencias_mulheres': 'Ocorrências em Mulheres',
    'ocorrencias_homens': 'Ocorrências em Homens',
    'soma_val_tot': 'Valor Total (R$)',
    'media_idade': 'Média de Idade',
    'IDHM': 'IDHM Geral',
    'IDHM Renda': 'IDHM Renda',
    'IDHM educacao': 'IDHM Educação',
    'IDHM Longevidade': 'IDHM Longevidade'
}

st.title("Mapa Interativo de Dados SUS por Município")

# Variáveis obrigatórias
st.subheader("Variáveis Obrigatórias")
# Depois (mostra CID + Descrição):
cid_com_descricao = dados[['cid_doenca', 'DESCRICAO']].drop_duplicates()
cid_com_descricao['opcoes'] = cid_com_descricao['cid_doenca'] + " - " + cid_com_descricao['DESCRICAO']

cid_selecionado_completo = st.selectbox(
    "Selecione a CID (Doença):",
    cid_com_descricao['opcoes']
)

# Extrai apenas o CID da seleção (para usar no filtro)
cid_doenca_selecionada = cid_selecionado_completo.split(" - ")[0]

# Filtra os dados
dados_filtrados = dados[dados['cid_doenca'] == cid_doenca_selecionada].copy()

# Variáveis opcionais
variaveis_selecionadas_nomes = st.multiselect(
    "Selecione variáveis para visualização:",
    options=list(nomes_amigaveis.values()),
    default=None
)

variaveis_selecionadas = [k for k, v in nomes_amigaveis.items() if v in variaveis_selecionadas_nomes]

if not variaveis_selecionadas:
    st.warning("Selecione pelo menos uma variável para visualizar o mapa.")
    st.stop()

# Pré-calcula valores extremos para normalização
valores_extremos = {
    var: {'min': dados_filtrados[var].min(), 'max': dados_filtrados[var].max()}
    for var in variaveis_selecionadas if pd.api.types.is_numeric_dtype(dados_filtrados[var])
}

# Criação do mapa
mapa = folium.Map(
    location=[dados_filtrados['latitude'].mean(), dados_filtrados['longitude'].mean()],
    zoom_start=6,
    tiles='CartoDB positron'
)

# Paleta de cores
cores_disponiveis = ['blue', 'red', 'green', 'purple', 'orange', 'pink', 'darkblue']

# Camada única para todos os marcadores (mais eficiente)
grupo_principal = folium.FeatureGroup(name="Dados SUS")

for _, row in dados_filtrados.iterrows():
    # Constrói o conteúdo do popup dinamicamente
    popup_content = f"""
    <div style="font-family: Arial; max-width: 300px;">
        <h4 style="margin-bottom: 5px;">{row['nome_municipio']}</h4>
        <p style="margin: 2px 0;"><b>CID:</b> {cid_doenca_selecionada}</p>
        <p style="margin: 2px 0;"><b>Descrição:</b> {row['DESCRICAO']}</p>  <!-- Nova linha -->
    """
    
    # Adiciona cada variável selecionada ao popup
    for var in variaveis_selecionadas:
        if pd.notna(row[var]):
            valor_formatado = f"{row[var]:.2f}" if isinstance(row[var], (int, float)) else row[var]
            popup_content += f'<p style="margin: 2px 0;"><b>{nomes_amigaveis[var]}:</b> {valor_formatado}</p>'
    
    popup_content += "</div>"
    
    # Cria marcador com círculos concêntricos
    for i, var in enumerate(variaveis_selecionadas):
        if pd.api.types.is_numeric_dtype(dados_filtrados[var]) and pd.notna(row[var]):
            # Normaliza o raio entre 5 e 20
            raio = 5 + 15 * (row[var] - valores_extremos[var]['min']) / (valores_extremos[var]['max'] - valores_extremos[var]['min'])
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=raio,
                color=cores_disponiveis[i % len(cores_disponiveis)],
                fill=True,
                fill_opacity=0.6,
                popup=folium.Popup(popup_content, max_width=350),
                stroke=False
            ).add_to(grupo_principal)

grupo_principal.add_to(mapa)
folium.LayerControl().add_to(mapa)

# Exibe o mapa
st_folium(mapa, width=1000, height=700)
