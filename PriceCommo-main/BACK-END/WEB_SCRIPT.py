import re
import requests
from datetime import date
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template





#.......................................................................................................................................................
#.......................................................................................................................................................





app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

def extrair_price(texto):
    # Procura pelo padrão R$ seguido de números, pontos ou vírgulas
    match = re.search(r'R\$\s*([\d.,]+)', texto)
    if match:
        # Retorna apenas o grupo 1, que é o número (ex: "130,50")
        return match.group(1).strip()
    return "N/A"


def limpar_texto(texto):
    texto = re.sub(r'\b(soja|milho|MILHO|SOJA)\b', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'[-\:\s\u200b]+', '', texto)  
    texto = texto.encode('utf-8').decode('utf-8') 
    return texto.strip()


def extrair_valores_min_max(texto_preco):
    numeros = re.findall(r'[\d]+[.,][\d]{2}', texto_preco)

    if len(numeros) == 2:
        return {"minima": numeros[0], "maxima": numeros[1]}
    elif len(numeros) == 1:
        return {"minima": numeros[0], "maxima": numeros[0]}
    else:
        return {"minima": "N/A", "maxima": "N/A"}
    

def calcular_media_preco(texto_preco):

    if not isinstance(texto_preco, str):
        return "N/A"

    numeros_str = [num.replace(',', '.') for num in re.findall(r'[\d]+[.,][\d]{2}', texto_preco)]
    
    if not numeros_str:
        return "N/A"

    numeros_float = [float(n) for n in numeros_str]

    media = sum(numeros_float) / len(numeros_float)

    return f"{media:.2f}".replace('.', ',')



#.......................................................................................................................................................
#.......................................................................................................................................................





def cotacao_agricolagemelli(): # DOIS SOUP
    url = 'https://agricolagemelli.com/historico-precos'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Agricolagemelli. {str(e)}", "url": url}
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('tr', class_='jet-dynamic-table__row')
        if len(price) > 1:
           dados = price[1].find_all('td')
           if len(dados) >= 3:
               soja = extrair_price(dados[1].get_text(strip=True)) if price[1] else "N/A"
               milho = extrair_price(dados[2].get_text(strip=True)) if price[2] else "N/A"
           else:
                soja = milho = "Valor não encotrado"
        else:
           soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Agricolagemelli",
            "Estado": "Paraná",
            "Cidade": "Cascavel"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Agricolagemelli: {str(e)}", "url": url}


def cotacao_camposverdes():
    url = 'https://www.camposverdes.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Campos Verdes: {str(e)}", "url": url}
    
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        
        data_element = soup.find('span', class_='pull-right font-ctc-dia')
        
        if data_element:
            
            data_text = data_element.get_text(strip=True)
            data = data_text.replace('- Manhã', '').strip()
        else:
            data = "N/A"
        price_elements = soup.find_all('div', class_='col-xs-3 col-sm-6 col-md-5 col-lg-4')
        
        soja = "N/A"
        milho = "N/A"

        if len(price_elements) >= 2:
            
            soja_text = price_elements[0].get_text(strip=True)
            milho_text = price_elements[1].get_text(strip=True)
            soja_match = re.search(r'R\$\s*[\d,.]+', soja_text)
            milho_match = re.search(r'R\$\s*[\d,.]+', milho_text)

            soja = extrair_price(soja_match.group(0)) if soja_match else "N/A"
            milho = extrair_price(milho_match.group(0)) if milho_match else "N/A"
        else:
            soja = milho = "Mercado está fechado"

        return {
            "Data": data,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Campos Verdes",
            "Estado": "Paraná",
            "Cidade": "Maringá"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Campos Verdes: {str(e)}", "url": url}
    

def cotacao_capaznet():
    url = 'https://www.capaznet.com/portal/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Capaznet: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('p')
        if len(price) >= 10:
            soja = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
            milho = extrair_price(price[2].get_text(strip=True)) if price[2] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Capaznet",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Não-me-Toque"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Capaznet: {str(e)}", "url": url}


def cotacao_cepalcereais():
    url = 'https://www.cepalcereais.com.br/'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Cepalcereais. {str(e)}", "url": url}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        data_hoje = date.today()
        data_hoje_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('p', style='text-shadow:#000 1px -1px, #000 -1px 1px, #000 1px 1px, #000 -1px -1px;')
        if len(price) >= 3:
            milho = limpar_texto(price[2].get_text(strip=True)) if price[2] else "N/A"
            soja = limpar_texto(price[0].get_text(strip=True)) if price[0] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_hoje_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Cepalcereais",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Não foi possível acessar os dados da Cepalcereais. {str(e)}", "url": url}


def cotacao_coagril():
    url = 'https://www.coagril-rs.com.br/cotacoes'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Coagril. {str(e)}", "url": url}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        data_hoje = date.today()
        data_hoje_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('td', class_='alignright')
        if len(price) >= 3:
            milho = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
            soja = extrair_price(price[3].get_text(strip=True)) if price[3] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_hoje_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Coagril",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Não foi possível acessar os dados da Coagril. {str(e)}", "url": url}


def cotacao_coopeagri():
    url = 'https://www.coopeagri.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Coopeagri. {str(e)}", "url": url}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        data_hoje = date.today()
        data_hoje_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('span', style='letter-spacing:normal;')
        if len(price) >= 5:
            milho = extrair_price(price[3].get_text(strip=True)) if price[3] else "N/A"
            soja = extrair_price(price[1].get_text(strip=True)).replace("c/ DAP", "").strip() if price[1] else "N/A"
        else:
            soja = milho = "---"
        return {
            "Data": data_hoje_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Coopeagri",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Não-me-Toque"
        }
    except Exception as e:
        return {"ERRO": f"Não foi possível acessar os dados da Coopeagri. {str(e)}", "url": url}


def cotacao_cotacoesmercado():
    url = 'https://www.cotacoesemercado.com/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Cotações & Mercado: {str(e)}", "url": url}
    
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        
        price_elements = soup.find_all('p', class_='font_8 wixui-rich-text__text')
        
        if len(price_elements) >= 10:
            # Extrai o texto completo de cada linha
            texto_soja_balcao = price_elements[1].get_text(strip=True)
            texto_milho_balcao = price_elements[2].get_text(strip=True)
            texto_soja_disponivel = price_elements[6].get_text(strip=True)
            texto_milho_disponivel = price_elements[7].get_text(strip=True)

            # Usa a nova função para calcular a média de cada um
            media_soja_balcao = calcular_media_preco(texto_soja_balcao)
            media_milho_balcao = calcular_media_preco(texto_milho_balcao)
            media_soja_disponivel = calcular_media_preco(texto_soja_disponivel)
            media_milho_disponivel = calcular_media_preco(texto_milho_disponivel)
        else:
            media_soja_balcao = media_milho_balcao = "N/A"
            media_soja_disponivel = media_milho_disponivel = "N/A"
            
        # Retorna o JSON com a estrutura de média, que é mais simples
        return {
            "Data": data_ptBR,
            "Balcão": {
                "Soja": media_soja_balcao,
                "Milho": media_milho_balcao
            },
            "Disponível": {
                "Soja": media_soja_disponivel,
                "Milho": media_milho_disponivel
            },
            "url": url,
            "Fonte": "Cotacoesemercado",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotações & Mercado: {str(e)}", "url": url}


def cotacao_cotriba():
    url = 'https://cotriba.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"erro": f"Não foi possível acessar os dados da Cotriba: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='content--value')
        if len(price) >= 3:
            milho = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
            soja = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Cotriba",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Não-me-Toque"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotriba: {str(e)}", "url": url}


def cotacao_cotrijal():
    url = 'https://www.cotrijal.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"erro": f"Não foi possível acessar os dados da Cotrijal: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', style='line-height: 45px;')
        if len(price) >= 3:
            milho = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
            soja = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
        else:
            soja = milho = "Mercado está fechado."
        return {
            "Data": data_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Cotrijal",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Não-me-Toque"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotrijal: {str(e)}", "url": url}


def cotacao_cotrirosa(): # ESSE TEM PREÇO PROXIMO, NÃO REAL
    url = 'https://cotrirosa.com/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestsException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Cotrirosa: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='content--value')
        if len(price) >= 3:
            soja = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
            milho = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Cotrirosa",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Santa Rosa"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotrirosa: {str(e)}", "url": url}
    

def cotacao_cotriel():
    url = 'https://www.cotriel.com.br/Home'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"erro": f"Não foi possível acessar os dados da Cotriba: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='well')
        if len(price) > 1:
            dados = price[1].find_all('p')
            if len(dados) >= 10:
                milho = extrair_price(dados[6].get_text(strip=True)) if dados[6] else "N/A"
                soja = extrair_price(dados[4].get_text(strip=True))if dados[4] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Soja": soja,
            "Milho": milho,
            "url": url,
            "Fonte": "Cotriel",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Não-me-Toque"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotriba: {str(e)}", "url": url}


def cotacao_cotrisal():
    url = 'https://www.cotrisal.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"erro": f"Não foi possível acessar os dados da Cotrisal: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('p', class_='preco_cotacao')
        if len(price) >= 6:
            norte_soja = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
            norte_milho = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
            noroeste_soja = extrair_price(price[3].get_text(strip=True)) if price[3] else "N/A"
            noroeste_milho = extrair_price(price[4].get_text(strip=True)) if price[4] else "N/A"
        else:
            norte_soja = norte_milho = "Mercado está fechado"
            noroeste_soja = noroeste_milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Regiao Norte": {
                "Soja": norte_soja,
                "Milho": norte_milho,
            },
            "Regiao Noroeste": {
                "Soja": noroeste_soja,
                "Milho": noroeste_milho,
            },
            "url": url,
            "Fonte": "Cotrisal",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotrisal: {str(e)}", "url": url}


def cotacao_cotrisoja():
    url = 'https://cotrisoja.com.br'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestsException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Cotrisoja: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='item--value')
        if len(price) >= 3:
            soja = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
            milho = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Cotrisoja",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cotrisoja: {str(e)}", "url": url}


def cotacao_grupopoletto():
    url = 'http://www.grupopoletto.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Grupo Poletto: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='col-xs-4')
        if len(price) >= 10:
            soja = extrair_price(price[4].get_text(strip=True)) if price[4] else "N/A"
            milho = extrair_price(price[8].get_text(strip=True)) if price[8] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Grupopoletto",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Não foi possível acessar os dados da Grupo Poletto: {str(e)}", "url": url}


def cotacao_plantarnet():
    url = 'https://www.plantarnet.com.br/agricola/cotacoes'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da PlantarNet: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('b')
        if len(price) >= 8:
            soja = extrair_price(limpar_texto(price[4].get_text(strip=True))) if price[4] else "N/A"
            milho = extrair_price(limpar_texto(price[5].get_text(strip=True))) if price[5] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Plantarnet",
            "Estado": "Paraná",
            "Cidade": "Cascavel"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da PlantarNet: {str(e)}", "url": url}
    

def cotacao_sebben():
    url = 'https://sebben.ind.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Sebben: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('span', class_='elementor-icon-list-text')
        if len(price) >= 8:
            soja = extrair_price(price[0].get_text(strip=True)).replace('-------------------------------------', '').strip() if price[0] else "N/A"
            milho = extrair_price(price[2].get_text(strip=True)).replace('-------------------------------------', '').strip() if price[2] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Sebben",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Passo Fundo"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Sebben: {str(e)}", "url": url}


def cotacao_cooperoque():
    url = 'https://www.cooperoque.com.br/?pg=cotacoes'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Cooperoque: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='el_3')
        if len(price) >= 3:
            soja = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
            milho = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Cooperoque",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Ijuí"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Cooperoque: {str(e)}", "url": url}


def cotacao_lazarotto():
    url = 'https://www.lazarotto.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Lazarotto: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('span', class_='exchange-price')
        if len(price) >= 3:
            soja = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
            milho = extrair_price(price[2].get_text(strip=True)) if price[2] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Lazarotto",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Ijuí"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Lazarotto: {str(e)}", "url": url}


def cotacao_grupouggeri():
    url = 'https://grupouggeri.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Grupouggeri: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='col-md-12 tcota')
        if len(price) >= 3:
            soja = extrair_price(price[0].get_text(strip=True)) if price[1] else "N/A"
            milho = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Grupouggeri",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Ijuí"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Grupouggeri: {str(e)}", "url": url}


def cotacao_vieraagrocereais():
    url = 'https://www.vieraagrocereais.com.br/'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Vieraagrocereais: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('span', class_='cotvalor')
        if len(price) >= 3:
            soja = price[0].get_text(strip=True) if price[0] else "N/A"
            milho = price[2].get_text(strip=True) if price[2] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Vieraagrocereais",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Ijuí"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Vieraagrocereais: {str(e)}", "url": url}


def cotacao_agropan():
    url = 'https://agropan.coop.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Agropan: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('div', class_='item--value')
        if len(price) >= 10:
            tarde_soja = extrair_price(limpar_texto(price[5].get_text(strip=True))) if price[5] else "N/A"
            tarde_milho = extrair_price(limpar_texto(price[2].get_text(strip=True))) if price[2] else "N/A"
            manha_soja = extrair_price(limpar_texto(price[1].get_text(strip=True))) if price[1] else "N/A"
            manha_milho = extrair_price(limpar_texto(price[6].get_text(strip=True))) if price[6] else "N/A"
        else:
            manha_soja = manha_milho = tarde_soja = tarde_milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Manhã" : {
                "Soja": manha_soja,
                "Milho": manha_milho
            },
            "Tarde" : {
                "Soja": tarde_soja,
                "Milho": tarde_milho
            },
            "Fonte": "Agropan",
            "url": url,
            "Estado": "Rio Grande do Sul",
            "Cidade": "Ijuí"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Agropan: {str(e)}", "url": url}


def cotacao_agriplanmga():
    url = 'http://www.agriplanmga.com.br/widgets/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Agriplanmga: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data = soup.find('span', class_='pull-left cotacaovalordata')
        data_str = data.get_text(strip=True) if data else "N/A"
        price = soup.find_all('span', class_='pull-left cotacaovalorsaca')
        if len(price) >= 3:
            milho = extrair_price(price[0].get_text(strip=True)) if price[0] else "N/A"
            soja = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_str,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Agriplanmga",
            "Estado": "Rio Grande do Sul",
            "Cidade": "Maringá"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Agriplanmga: {str(e)}", "url": url}


def cotacao_coagru():
    url = 'https://www.coagru.com.br/'
    try:
        response = requests.get(url, timeout=10 )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ERRO": f"Não foi possível acessar os dados da Coagru: {str(e)}", "url": url}
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    try:
        data_hoje = date.today()
        data_ptBR = data_hoje.strftime("%d/%m/%Y")
        price = soup.find_all('td', colspan='3')
        if len(price) >= 3:
            milho = extrair_price(price[2].get_text(strip=True)) if price[2] else "N/A"
            soja = extrair_price(price[1].get_text(strip=True)) if price[1] else "N/A"
        else:
            soja = milho = "Mercado está fechado"
        return {
            "Data": data_ptBR,
            "Milho": milho,
            "Soja": soja,
            "url": url,
            "Fonte": "Coagru",
            "Estado": "Paraná",
            "Cidade": "Cascavel"
        }
    except Exception as e:
        return {"ERRO": f"Erro ao processar dados da Coagru: {str(e)}", "url": url}

#.......................................................................................................................................................
#.......................................................................................................................................................





# Endpoints da API
@app.route('/')
def index():
    return render_template('HOME.html')

@app.route('/commodities')
def commodities():
    return render_template('COMMODITIES.html')

@app.route('/sites')
def sites():
    return render_template('INSIDE_SITES.html')

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "API de Cotações Agrícolas",
        "endpoints": [

            # RIO GRANDE DO SUL
            #//////////////////////////////////////////////////////////////
            # PASSO FUNDO
            "/cotacao/cepalcereais", # RIO GRANDE DO SUL / Passo Fundo
            "/cotacao/coagril", # RIO GRANDE DO SUL / Passo Fundo
            "/cotacao/cotacoesmercado", # RIO GRANDE DO SUL / Passo Fundo
            "/cotacao/cotrisal", # RIO GRANDE DO SUL / Passo Fundo
            "/cotacao/cotrisoja", # RIO GRANDE DO SUL / Passo Fundo
            "/cotacao/grupopoletto", # RIO GRANDE DO SUL / Passo Fundo
            "/cotacao/sebben", # RIO GRANDE DO SUL / Passo Fundo
            # NÃO-ME-TOQUE
            "/cotacao/capaznet", # RIO GRANDE DO SUL / Não-me-Toque
            "/cotacao/cotriba", # RIO GRANDE DO SUL / Não-me-Toque
            "/cotacao/cotriel", # RIO GRANDE DO SUL / Não-me-Toque
            "/cotacao/cotrijal", # RIO GRANDE DO SUL / Não-me-Toque
            "/cotacao/coopeagri", # RIO GRANDE DO SUL / Não-me-Toque
            # SANTA ROSA
            "/cotacao/cotrirosa", # RIO GRANDE DO SUL / Santa Rosa
            # IJUÍ
            "/cotacao/cooperoque", # RIO GRANDE DO SUL / Ijuí
            "/cotacao/lazarotto", # RIO GRANDE DO SUL / Ijuí
            "/cotacao/grupouggeri", # RIO GRANDE DO SUL / Ijuí
            "/cotacao/vieraagrocereais", # RIO GRANDE DO SUL / Ijuí
            "/cotacao/agropan", # RIO GRANDE DO SUL / Ijuí
            #///////////////////////////////////////////////////////////////

            # PARANÁ
            #///////////////////////////////////////////////////////////////
            # CASCAVEL
            "/cotacao/agricolagemelli", # PARANÁ / Cascavel
            "/cotacao/plantarnet", # PARANÁ / Cascavel
            "/cotacao/coagru", #PARANÁ / Cascavel
            # MARINGÁ
            "/cotacao/agriplanmga", # PARANÁ / Maringá
            #///////////////////////////////////////////////////////////////

            # OUTROS
            "/cotacao/camposverdes",

            # COTAÇÕES DE OUTROS ESTADOS
            "/cotacao/rio_grande_do_sul",
            "/cotacao/parana",
            "/cotacao/rio_grande_do_sul/passo_fundo",
            "/cotacao/rio_grande_do_sul/nao_me_toque",
            "/cotacao/rio_grande_do_sul/santa_rosa",
            "/cotacao/rio_grande_do_sul/ijui",
            "/cotacao/parana/cascavel",
            "/cotacao/parana/maringa",
            "/cotacao/todas"
        ]
    })





#.......................................................................................................................................................
#.......................................................................................................................................................





@app.route('/cotacao/agricolagemelli', methods=['GET'])
def api_cotacao_agricolagemelli():
    resultado = cotacao_agricolagemelli()
    return jsonify(resultado)


@app.route('/cotacao/camposverdes', methods=['GET'])
def api_cotacao_camposverdes():
    resultado = cotacao_camposverdes()
    return jsonify(resultado)


@app.route('/cotacao/cepalcereais', methods=['GET'])
def api_cotacao_cepalcereais():
    resultado = cotacao_cepalcereais()
    return jsonify(resultado)


@app.route('/cotacao/capaznet', methods=['GET'])
def api_cotacao_capaznet():
    resultado = cotacao_capaznet()
    return jsonify(resultado)


@app.route('/cotacao/coagril', methods=['GET'])
def api_cotacao_coagril():
    resultado = cotacao_coagril()
    return jsonify(resultado)


@app.route('/cotacao/cotrijal', methods=['GET'])
def api_cotacao_cotrijal():
    resultado = cotacao_cotrijal()
    return jsonify(resultado)


@app.route('/cotacao/cotacoesmercado', methods=['GET'])
def api_cotacao_cotacoesmercado():
    resultado = cotacao_cotacoesmercado()
    return jsonify(resultado)


@app.route('/cotacao/cotriba', methods=['GET'])
def api_cotacao_cotriba():
    resultado = cotacao_cotriba()
    return jsonify(resultado)


@app.route('/cotacao/cotriel', methods=['GET'])
def api_cotacao_cotriel():
    resultado = cotacao_cotriel()
    return jsonify(resultado)


@app.route('/cotacao/cotrisal', methods=['GET'])
def api_cotacao_cotrisal():
    resultado = cotacao_cotrisal()
    return jsonify(resultado)


@app.route('/cotacao/cotrisoja', methods=['GET'])
def api_cotacao_cotrisoja():
    resultado = cotacao_cotrisoja()
    return jsonify(resultado)


@app.route('/cotacao/cotrirosa', methods=['GET'])
def api_cotacao_cotrirosa():
    resultado = cotacao_cotrirosa()
    return jsonify(resultado)


@app.route('/cotacao/coopeagri', methods=['GET'])
def api_cotacao_coopeagri():
    resultado = cotacao_coopeagri()
    return jsonify(resultado)


@app.route('/cotacao/grupopoletto', methods=['GET'])
def api_cotacao_grupopoletto():
    resultado = cotacao_grupopoletto()
    return jsonify(resultado)


@app.route('/cotacao/plantarnet', methods=['GET'])
def api_cotacao_plantarnet():
    resultado = cotacao_plantarnet()
    return jsonify(resultado)


@app.route('/cotacao/sebben', methods=['GET'])
def api_cotacao_sebben():
    resultado = cotacao_sebben()
    return jsonify(resultado)


@app.route('/cotacao/cooperoque', methods=['GET'])
def api_cotacao_cooperoque():
    resultado = cotacao_cooperoque()
    return jsonify(resultado)


@app.route('/cotacao/lazarotto', methods=['GET'])
def api_cotacao_lazarotto():
    resultado = cotacao_lazarotto()
    return jsonify(resultado)


@app.route('/cotacao/grupouggeri', methods=['GET'])
def api_cotacao_grupouggeri():
    resultado = cotacao_grupouggeri()
    return jsonify(resultado)


@app.route('/cotacao/vieraagrocereais', methods=['GET'])
def api_cotacao_vieraagrocereais():
    resultado = cotacao_vieraagrocereais()
    return jsonify(resultado)


@app.route('/cotacao/agropan', methods=['GET'])
def api_cotacao_agropan():
    resultado = cotacao_agropan()
    return jsonify(resultado)


@app.route('/cotacao/agriplanmga', methods=['GET'])
def api_cotacao_agriplanmga():
    resultado = cotacao_agriplanmga()
    return jsonify(resultado)


@app.route('/cotacao/coagru', methods=['GET'])
def api_cotacao_coagru():
    resultado = cotacao_coagru()
    return jsonify(resultado)


#.......................................................................................................................................................
#.......................................................................................................................................................



@app.route('/cotacao/rio_grande_do_sul', methods=['GET'])
def api_cotacao_rio_grande_do_sul():
    return jsonify({
        "cepalcereais": cotacao_cepalcereais(), # RIO GRANDE DO SUL / Passo Fundo
        "coagril": cotacao_coagril(), # RIO GRANDE DO SUL / Passo Fundo
        "cotacoesmercado": cotacao_cotacoesmercado(), # RIO GRANDE DO SUL / Passo Fundo
        "cotrisal": cotacao_cotrisal(), # RIO GRANDE DO SUL / Passo Fundo
        "cotrisoja": cotacao_cotrisoja(), # RIO GRANDE DO SUL / Passo Fundo
        "grupopoletto": cotacao_grupopoletto(), # RIO GRANDE DO SUL / Passo Fundo
        "sebben": cotacao_sebben(), # RIO GRANDE DO SUL / Passo Fundo
        "capaznet": cotacao_capaznet(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotriba": cotacao_cotriba(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotriel": cotacao_cotriel(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotrijal": cotacao_cotrijal(), # RIO GRANDE DO SUL / Não-me-Toque
        "coopeagri": cotacao_coopeagri(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotrirosa": cotacao_cotrirosa(), # RIO GRANDE DO SUL / Santa Rosa
    })





@app.route('/cotacao/parana', methods=['GET'])
def api_cotacao_parana():
    return jsonify({
        "agricolagemelli": cotacao_agricolagemelli(), # PARANÁ / Cascavel
        "plantarnet": cotacao_plantarnet(), # PARANÁ / Cascavel
        "agriplanmga": cotacao_agriplanmga() # PARANÁ / Maringá
    })








@app.route('/cotacao/rio_grande_do_sul/passo_fundo', methods=['GET']) #OK, 1º
def api_cotacao_passo_fundo():
    return jsonify({ 
        "cepalcereais": cotacao_cepalcereais(), # RIO GRANDE DO SUL / Passo Fundo
        "coagril": cotacao_coagril(), # RIO GRANDE DO SUL / Passo Fundo
        "cotacoesmercado": cotacao_cotacoesmercado(), # RIO GRANDE DO SUL / Passo Fundo
        "cotrisal": cotacao_cotrisal(), # RIO GRANDE DO SUL / Passo Fundo
        "cotrisoja": cotacao_cotrisoja(), # RIO GRANDE DO SUL / Passo Fundo
        "grupopoletto": cotacao_grupopoletto(), # RIO GRANDE DO SUL / Passo Fundo
        "sebben": cotacao_sebben() # RIO GRANDE DO SUL / Passo Fundo
    })






@app.route('/cotacao/rio_grande_do_sul/nao_me_toque', methods=['GET']) #OK, 2º
def api_cotacao_nao_me_toque():
    return jsonify({
        "capaznet": cotacao_capaznet(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotriba": cotacao_cotriba(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotriel": cotacao_cotriel(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotrijal": cotacao_cotrijal(), # RIO GRANDE DO SUL / Não-me-Toque
        "coopeagri": cotacao_coopeagri() # RIO GRANDE DO SUL / Não-me-Toque
    })





@app.route('/cotacao/rio_grande_do_sul/santa_rosa', methods=['GET']) #OK, 3º
def api_cotacao_santa_rosa():
    return jsonify({
        "cotrirosa": cotacao_cotrirosa() # RIO GRANDE DO SUL / Santa Rosa
    })






@app.route('/cotacao/rio_grande_do_sul/ijui', methods=['GET']) #OK, 4º
def api_cotacao_ijui():
    return jsonify({
        "cooperoque": cotacao_cooperoque(), # RIO GRANDE DO SUL / Ijuí
        "lazarotto": cotacao_lazarotto(), # RIO GRANDE DO SUL / Ijuí / TEM HORÁRIO DE PREÇO
        "grupouggeri": cotacao_grupouggeri(), # RIO GRANDE DO SUL / Ijuí / TEM HORÁRIO DE PREÇO
        "vieraagrocereais": cotacao_vieraagrocereais(), # RIO GRANDE DO SUL / Ijuí
        "agropan": cotacao_agropan() # RIO GRANDE DO SUL / Ijuí
    })






@app.route('/cotacao/parana/cascavel', methods=['GET']) #OK, 5º
def api_cotacao_cascavel():
    return jsonify({
        "agricolagemelli": cotacao_agricolagemelli(), # PARANÁ / Cascavel
        "plantarnet": cotacao_plantarnet(), # PARANÁ / Cascavel
        "coagru": cotacao_coagru() # PARANÁ / Cascavel
    })





@app.route('/cotacao/parana/maringa', methods=['GET']) #OK, 6º
def api_cotacao_maringa():
    return jsonify({
        "agriplanmga": cotacao_agriplanmga(), # PARANÁ / Maringá
        "camposverdes": cotacao_camposverdes() # PARANÁ / Maringá
    })







#.......................................................................................................................................................
#.......................................................................................................................................................





@app.route('/cotacao/todas', methods=['GET'])
def api_cotacao_todas():
    """Endpoint que retorna todas as cotações de uma vez"""
    return jsonify({
        # RIO GRANDE DO SUL
        "cepalcereais": cotacao_cepalcereais(), # RIO GRANDE DO SUL / Passo Fundo
        "coagril": cotacao_coagril(), # RIO GRANDE DO SUL / Passo Fundo
        "cotacoesmercado": cotacao_cotacoesmercado(), # RIO GRANDE DO SUL / Passo Fundo
        "cotrisal": cotacao_cotrisal(), # RIO GRANDE DO SUL / Passo Fundo
        "cotrisoja": cotacao_cotrisoja(), # RIO GRANDE DO SUL / Passo Fundo
        "grupopoletto": cotacao_grupopoletto(), # RIO GRANDE DO SUL / Passo Fundo
        "sebben": cotacao_sebben(), # RIO GRANDE DO SUL / Passo Fundo
        "capaznet": cotacao_capaznet(), #RIO GRANDE DO SUL / Não-me-Toque
        "cotriba": cotacao_cotriba(), #RIO GRANDE DO SUL / Não-me-Toque
        "cotriel": cotacao_cotriel(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotrijal": cotacao_cotrijal(), # RIO GRANDE DO SUL / Não-me-Toque
        "coopeagri": cotacao_coopeagri(), # RIO GRANDE DO SUL / Não-me-Toque
        "cotrirosa": cotacao_cotrirosa(), # RIO GRANDE DO SUL / Santa Rosa
        "cooperoque": cotacao_cooperoque(), # RIO GRANDE DO SUL / Ijuí
        "lazarotto": cotacao_lazarotto(), # RIO GRANDE DO SUL / Ijuí
        "grupouggeri": cotacao_grupouggeri(), # RIO GRANDE DO SUL / Ijuí
        "vieraagrocereais": cotacao_vieraagrocereais(), # RIO GRANDE DO SUL / Ijuí
        "agropan": cotacao_agropan(), # RIO GRANDE DO SUL / Ijuí
        # PARANÁ
        "agricolagemelli": cotacao_agricolagemelli(), # PARANÁ / Cascavel
        "plantarnet": cotacao_plantarnet(), # PARANÁ / Cascavel
        "coagru": cotacao_coagru(), # PARANÁ / Cascavel
        "agriplanmga": cotacao_agriplanmga(), # PARANÁ / Maringá
        "camposverdes": cotacao_camposverdes() # PARANÁ / Maringá

    })

if __name__ == '__main__':
   app.run(debug=True)

#.......................................................................................................................................................
#.......................................................................................................................................................
