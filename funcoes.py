import numpy as np
import functools as ft
from itertools import permutations

# FUNCOES PARA BUSCAR DADOS DOS ARQUIVOS
def separa_numeros(linha):
    simbolos = ['<=','>=', '==']
    return [float(val.replace(',', '.')) if ',' in val else val if val in simbolos else float(val) for val in linha.split()]


def gera_dicionario_dados(lista_chaves, linha):
    return {chave: valor for chave, valor in zip(lista_chaves, separa_numeros(linha))}


def le_arquivo(nome_arquivo):
    tratamento_funcao = {
        '0': lambda linha: {'meta': gera_dicionario_dados(['num_restricao', 'num_var_original', 'sentido_otimizacao'], linha)},
        '1': lambda linha: {'coeficiente': separa_numeros(linha)},
        'sa': lambda linhas: [separa_numeros(linha) for linha in linhas],
        'solucao_otima': lambda linha: {'solucao_otima': separa_numeros(linha)}
    }
    dicionario_arquivo = {}
    with open(nome_arquivo, 'r') as arquivo:
        linhas = [linha.strip() for linha in arquivo]
        for i in range(2):
            dicionario_arquivo.update(tratamento_funcao[f"{i}"](linhas[i]))

        num_restricao = int(dicionario_arquivo['meta']['num_restricao'])
        dicionario_arquivo['sa'] = tratamento_funcao['sa'](linhas[2:2+num_restricao])
        eh_solucao = False
        for linha in linhas:
            if eh_solucao:
                dicionario_arquivo['solucao'] = separa_numeros(linha)
                break
            if '//' in linha:
                continue
        return dicionario_arquivo

# FUNCOES PARA REALIZAR CALCULOS DE MATRIZES

# FUNCOES PARA MANIPULAR COLUNAS
def pega_coluna(tabela, indice):
  coluna = [linha[indice] for linha in tabela]
  return coluna

def pega_coluna_pivo(sobra, tabela):
  tabela_sem_ultima_coluna = [linha[:-1] for linha in tabela]
  ultima_linha = tabela_sem_ultima_coluna[-1]
  index = ultima_linha.index(min(ultima_linha))
  return pega_coluna(tabela, index)

def pega_index_coluna(coluna_pivo, tabela):
  index = None
  for j in range(len(coluna_pivo)):
    resultado = True
    for i in range(len(tabela)):
      resultado = resultado and tabela[i][j] == coluna_pivo[i]
    if resultado:
      index = j
      break
  return index

def verifica_coluna_identidade(coluna, index_1):
  resultado = True
  for i in coluna:
    if coluna.index(i) == index_1:
      resultado = resultado and i == 1.0
    else:
      resultado = resultado and i == 0.0
  return resultado


#FUNCOES PARA MANIPULAR LINHAS
def pega_linha_que_vai_sair(pivo, tabela):
  ultima_coluna = [linha[-1] for linha in tabela]
  razao = []
  for i in range(len(pivo)):
    valor = round(ultima_coluna[i]/pivo[i], 2) if pivo[i] != 0 else 0.0
    razao.append(valor)
  razao = list(filter(lambda valor: valor > 0, razao))
  index_menor_valor = razao.index(min(razao))
  return tabela[index_menor_valor]

def calcula_valor_para_1(linha, indice_coluna_sair, tabela):
  valor = linha[indice_coluna_sair]
  if valor == 0:
    linha_selecionada = []
    for linha in tabela:
      if linha[indice_coluna_sair] != 0:
        linha_selecionada = linha
        break
    valor = linha_selecionada[indice_coluna_sair]
    linha_selecionada = list(map(lambda valor_linha: round(valor_linha/valor, 2), linha_selecionada))
    return [linha[i] + linha_selecionada[i] for i in range(len(linha))]

  return list(map(lambda val: val/valor, linha))

def calcula_valor_para_0(linha, linha_base, indice_coluna_sair):
  razao = linha[indice_coluna_sair]/linha_base[indice_coluna_sair]
  linha_base_multiplicada_pela_razao = list(map(lambda x: x*razao, linha_base))
  return [linha[i]-linha_base_multiplicada_pela_razao[i] for i in range(len(linha))]

def transformacoes_lineares_big_M(tabela, indices_coluna_M):
  colunas_M = [pega_coluna(tabela, indice) for indice in indices_coluna_M]
  linhas_M = []
  for i in range(len(tabela)):
    for indice in indices_coluna_M:
      if tabela[i][indice] == 1:
        linhas_M.append(i)
  ultima_linha = tabela[-1]
  for i in range(len(indices_coluna_M)):
    ultima_linha = calcula_valor_para_0(ultima_linha, tabela[linhas_M[i]], indices_coluna_M[i])
  tabela[-1] = ultima_linha
  return tabela

# FUNCOES DE MANIPULACAO DE MATRIZ SEGUINDO AS REGRAS DO TRABALHO
M = 10000.0
def trata_expressao_com_b_negativo(A, b, sinal):
  sinal_inverso = {'<=':'>=', '>=':'<=', '==':'=='}
  if b < 0:
    A = list(map(lambda valor: valor*(-1), A))
    b = b*(-1)
    sinal = sinal_inverso[sinal]
  return A, b, sinal

def metodo_big_Mac(coeficientes, qtd_var_artificiais):
  pos = -2
  eh_caso_big_M = False
  while qtd_var_artificiais > 0:
    eh_caso_big_M = True
    coeficientes[pos] = M
    pos -= 1
    qtd_var_artificiais -= 1
  return coeficientes, eh_caso_big_M

def ajusta_fo(fo, sa_canonico, sentido, qtd_var_artificiais):
  diferenca = len(sa_canonico[0]) - len(fo)
  if sentido:
    fo = list(map(lambda valor: valor*(-1), fo))
  for i in range(diferenca):
    fo.append(0.0)
  return metodo_big_Mac(fo, qtd_var_artificiais)

def ajusta_forma_canonica_big_M(matriz_canonica, qtd_variaveis_artificiais):
  indices_coluna_M = []
  ultima_linha = matriz_canonica[-1]
  for i in range(len(ultima_linha)):
    if ultima_linha[i] == M:
      indices_coluna_M.append(i)
  matriz_canonica = transformacoes_lineares_big_M(matriz_canonica, indices_coluna_M)
  return matriz_canonica

def forma_canonica(sa, index_sinal, dados):
  fo = dados['coeficiente']
  sentido = int(dados['meta']['sentido_otimizacao'])
  qtd_variaveis = qtd_variaveis = int(dados['meta']['num_var_original'])
  index_sinal = qtd_variaveis
  A = list(map(lambda expressao: expressao[:index_sinal], sa))
  b = list(map(lambda expressao: expressao[-1], sa))
  sinais = list(map(lambda expressao: expressao[index_sinal], sa))
  valor_sinal = {'<=':1.0,'>=':-1.0,'==':0.0}
  matriz_canonica = []
  qtd_variaveis_artificiais = 0
  for i in range(len(sa)):
    A[i], b[i], sinais[i] = trata_expressao_com_b_negativo(A[i],b[i],sinais[i])
    valor = valor_sinal[sinais[i]]
    for j in range(len(sa)):
      A[j].append(valor if i==j else 0.0)
  for i in range(len(sa)):
    if sinais[i] == '>=':
      qtd_variaveis_artificiais += 1
      for j in range(len(sa)):
        A[j].append(1.0 if i == j else 0.0)
  for i in range(len(sa)):
      matriz_canonica.append(A[i] + [b[i]])
  fo, eh_caso_big_M = ajusta_fo(fo, matriz_canonica, sentido, qtd_variaveis_artificiais)
  matriz_canonica.append(fo)
  if eh_caso_big_M:
    matriz_canonica = ajusta_forma_canonica_big_M(matriz_canonica, qtd_variaveis_artificiais)
  return matriz_canonica

def monta_base(tabela, num_restricoes, indices_colunas):
  tabela_sem_ultima_coluna = [linha[:-1] for linha in tabela]
  A = tabela_sem_ultima_coluna[:-1]
  base = [[] for linha in A]
  sobra = [[] for linha in A]
  for j in indices_colunas:
    for i in range(len(A)):
      base[i].append(A[i][j])
  indices_sobra = [i for i in range(len(A[0])) if i not in indices_colunas]
  for j in indices_sobra:
    for i in range(len(A)):
      sobra[i].append(A[i][j])
  return base, sobra, indices_colunas

def verifica_se_eh_identidade(base):
  resultado = True
  for i in range(len(base)):
    for j in range(len(base[i])):
      if i == j:
        resultado = resultado and (base[i][j] == 1.0 or base[i][j] == -1.0)
      else:
        resultado = resultado and base[i][j] == 0.0
  return resultado

def imprime_tabela(tabela):
  print('[')
  for linha in tabela:
    print(linha)
  print(']')

def gera_matriz_identidade(base, coluna_pivo, linha_pivo, index_coluna_pivo, num_restricoes, indice_colunas, tabela):
  index = tabela.index(linha_pivo)
  tabela[index] = calcula_valor_para_1(linha_pivo, index_coluna_pivo, tabela)
  sobra = []
  while True:
    for i in range(len(tabela)):
      if i == index:
        continue
      tabela[i] = calcula_valor_para_0(tabela[i], tabela[index], index_coluna_pivo)
    nova_base, sobra, indice_colunas = monta_base(tabela, num_restricoes, indice_colunas)
    if verifica_se_eh_identidade(nova_base):
      break
  return nova_base, sobra, tabela

# FUNCOES QUE JA ESTAO MAIS DIRETAMENTE RELACIONADAS A LOGICA DO PROJETO
def tratamento_inicial(dados):
  sa = dados['sa']
  qtd_variaveis = int(dados['meta']['num_var_original'])
  matriz_canonica = forma_canonica(sa, qtd_variaveis, dados)
  return matriz_canonica

def monta_base_inicial(tabela, numero_restricoes):
  tabela_sem_ultima_coluna = [linha[:-1] for linha in tabela]
  tabela_sem_ultima_linha = tabela_sem_ultima_coluna[:-1]
  indices = [i for i in range(len(tabela_sem_ultima_linha[0]))]
  indice_colunas = []
  pos_indice = 0 #REFERE-SE A POSICAO NA COLUNA QUE DEVERIA TER O VALOR 1.0
  while pos_indice < len(tabela_sem_ultima_linha):
    for i in indices:
      coluna = pega_coluna(tabela_sem_ultima_linha, i)
      if verifica_coluna_identidade(coluna, pos_indice):
        indice_colunas.append(i)
        pos_indice += 1
  return monta_base(tabela, numero_restricoes, indice_colunas)

def existe_var_nao_basica_melhora_fo(sobra, tabela):
  ultima_linha = sobra[-1]
  menor_valor = min(ultima_linha)
  return menor_valor < 0

def existe_var_basica_para_sair(base, coluna_pivo, tabela):
  b = [linha[-1] for linha in tabela]
  razao = []
  for i in range(len(coluna_pivo)):
    if coluna_pivo[i] != 0.0:
      razao.append(b[i]/coluna_pivo[i])
    else:
      razao.append(0.0)
  resultados_positivos = list(filter(lambda x: x>0, razao))
  return resultados_positivos != []

def trocar_variaveis(base, sobra, linha_pivo, coluna_pivo, num_restricoes, indice_colunas, tabela):
  # LINHA_PIVO => COLUNA DA BASE QUE VAI SAIR
  # COLUNA_PIVO => A A LINHA DA SOBRA QUE VAI ENTRAR
  # A COLUNA_PIVO TERA DE SER ALTERADA PARA QUE FIQUE O MAIS PROXIMO DA IDENTIDADE
  b = [linha[-1] for linha in tabela]
  index_linha_sair = tabela.index(linha_pivo)
  index_coluna_pivo = pega_index_coluna(coluna_pivo, tabela)
  indice_colunas[index_linha_sair] = index_coluna_pivo
  base, sobra, tabela = gera_matriz_identidade(base, coluna_pivo, linha_pivo, index_coluna_pivo, num_restricoes, indice_colunas, tabela)
  return base, sobra, tabela


def simplex(dados):
  tabela = tratamento_inicial(dados)
  num_restricoes = int(dados['meta']['num_restricao'])
  base, sobra, indice_colunas = monta_base_inicial(tabela, num_restricoes)
  while existe_var_nao_basica_melhora_fo(sobra, tabela):
    coluna_pivo = pega_coluna_pivo(sobra, tabela)
    linha_pivo = pega_linha_que_vai_sair(coluna_pivo, tabela)
    base, sobra, tabela = trocar_variaveis(base, sobra, linha_pivo, coluna_pivo, num_restricoes, indice_colunas, tabela)
    if not existe_var_basica_para_sair(base, coluna_pivo, tabela):
      return f'O PPL é ilimitado'
    imprime_tabela(coluna_pivo)
  return f'Solucao Otima: {base}'

def executa(arquivo):
  dados = le_arquivo(arquivo)
  return simplex(dados)