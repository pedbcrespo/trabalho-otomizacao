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
def trata_expressao_com_b_negativo(A, b, sinal):
  sinal_inverso = {'<=':'>=', '>=':'<=', '==':'=='}
  if b < 0:
    A = list(map(lambda valor: valor*(-1), A))
    b = b*(-1)
    sinal = sinal_inverso[sinal]
  return A, b, sinal

def forma_canonica(sa, index_sinal):
  A = list(map(lambda expressao: expressao[:index_sinal], sa))
  b = list(map(lambda expressao: expressao[-1], sa))
  sinais = list(map(lambda expressao: expressao[index_sinal], sa))
  valor_sinal = {'<=':1.0,'>=':-1.0,'==':0.0}
  for i in range(len(sa)):
    A[i], b[i], sinais[i] = trata_expressao_com_b_negativo(A[i],b[i],sinais[i])
    valor = valor_sinal[sinais[i]]
    for j in range(len(sa)):
      A[j].append(valor if i==j else 0.0)
  matriz_canonica = []
  for i in range(len(sa)):
    matriz_canonica.append(A[i] + [b[i]])
  return matriz_canonica, A, b

def ajusta_fo(fo, sa_canonico, sentido):
  diferenca = len(sa_canonico[0]) - len(fo)
  if sentido:
    fo = list(map(lambda valor: valor*(-1), fo))
  for i in range(diferenca):
    fo.append(0.0)
  return fo

def tratamento_inicial(dados):
  fo = dados['coeficiente']
  sa = dados['sa']
  sentido = int(dados['meta']['sentido_otimizacao'])
  qtd_variaveis = int(dados['meta']['num_var_original'])
  sa_canonico, A, b = forma_canonica(sa, qtd_variaveis)
  fo_completo_com_zeros = ajusta_fo(fo, sa_canonico, sentido)
  sa_canonico.append(fo_completo_com_zeros)
  return sa_canonico

def monta_base_inicial(tabela, numero_restricoes):
  base = []
  tabela_sem_ultima_coluna = [linha[:-1] for linha in tabela]
  A = tabela_sem_ultima_coluna[:-1]
  base = [linha[-numero_restricoes:] for linha in A]
  sobra = [linha[:-numero_restricoes] for linha in tabela_sem_ultima_coluna]
  indice_colunas = [i for i in range(len(A[0]))][-numero_restricoes:]
  return base, sobra, indice_colunas

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
  return base, sobra

def pega_linha_que_vai_sair(pivo, tabela):
  ultima_coluna = [linha[-1] for linha in tabela]
  razao = []
  for i in range(len(pivo)):
    valor = round(ultima_coluna[i]/pivo[i], 2) if pivo[i] != 0 else 0.0
    razao.append(valor)
  razao = list(filter(lambda valor: valor > 0, razao))
  index_menor_valor = razao.index(min(razao))
  return tabela[index_menor_valor]
  

def pega_coluna_pivo(sobra, tabela):
  ultima_linha = tabela[-1]
  index = ultima_linha.index(min(ultima_linha))
  print('index', index)
  return [linha[index] for linha in sobra]


def existe_var_nao_basica_melhora_fo(sobra, tabela):
  ultima_linha = sobra[-1]
  menor_valor = min(ultima_linha)
  return menor_valor < 0

def existe_var_basica_para_sair(base, tabela):
  pass

def calcula_valor_para_1(linha, indice_coluna_sair, tabela):
  valor = linha[indice_coluna_sair]
  if valor == 0:
    linha_selecionada = []
    for linha in tabela:
      if linha[indice_coluna_sair] != 0:
        linha_selecionada = linha
        break
    valor = linha_selecionada[indice_coluna_sair]
    linha_selecionada = list(map(lambda valor_linha: valor_linha/valor, linha_selecionada))
    return [linha[i] + linha_selecionada[i] for i in range(len(linha))]

  return list(map(lambda val: val/valor, linha))

def calcula_valor_para_0(linha, linha_base, indice_coluna_sair):
  razao = linha[indice_coluna_sair]/linha_base[indice_coluna_sair]
  linha_base_multiplicada_pela_razao = list(map(lambda x: x*razao, linha_base))
  return [linha[i]-linha_base_multiplicada_pela_razao[i] for i in range(len(linha))]

def eh_identidade(base):
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
    nova_base, sobra = monta_base(tabela, num_restricoes, indice_colunas)
    if eh_identidade(nova_base):
      break
  return nova_base, sobra, tabela

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
    if not existe_var_basica_para_sair(base, tabela):
      return f'O PPL é ilimitado'
    coluna_pivo = pega_coluna_pivo(sobra, tabela)
    linha_pivo = pega_linha_que_vai_sair(coluna_pivo, tabela)
    base, sobra, tabela = trocar_variaveis(base, sobra, linha_pivo, coluna_pivo, num_restricoes, indice_colunas, tabela)
  return f'Solucao Otima: {base}'