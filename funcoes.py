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
  contador = 0
  tabela_sem_ultima_coluna = [linha[:-1] for linha in tabela]
  A = tabela_sem_ultima_coluna[:-1]
  base = [linha[-numero_restricoes:] for linha in A]
  sobra = [linha[:-numero_restricoes] for linha in tabela_sem_ultima_coluna]
  return base, sobra

def pega_linha_pivo(pivo, tabela):
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
  return [linha[index] for linha in sobra]

def existe_var_nao_basica_melhora_fo(sobra, tabela):
  ultima_linha = sobra[-1]
  menor_valor = min(ultima_linha)
  return menor_valor < 0

def existe_var_basica_para_sair(base, tabela):
  pass

def trocar_variaveis(base, sobra, linha_pivo, coluna_pivo, tabela):
  # LINHA_PIVO => COLUNA DA BASE QUE VAI SAIR
  # COLUNA_PIVO => A A LINHA DA SOBRA QUE VAI ENTRAR
  # A COLUNA_PIVO TERA DE SER ALTERADA PARA QUE FIQUE O MAIS PROXIMO DA IDENTIDADE
  print('base ',base)
  print('sobra', sobra)
  print('linha pivo', linha_pivo)
  print('coluna pivo', coluna_pivo)
  linha_pivo = linha_pivo[:len(sobra[0])]
  index_coluna_sair = sobra.index(linha_pivo)

  for i in range(len(base)):
    base[i][index_coluna_sair] = linha_pivo[i]
  return base