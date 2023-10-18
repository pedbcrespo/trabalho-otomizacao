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
def adiciona_valor_A(A, exp, valor):
    for a in A:
        if a == exp:
            a.append(valor)
        else:
            a.append(0.0)
    return A

def forma_canonica(A, sinal):
    novo_A = A
    for i in range(len(A)):
        if sinal[i] == '<=':
            novo_A = adiciona_valor_A(novo_A, novo_A[i], 1.0)
        elif sinal[i] == '>=':
            novo_A = adiciona_valor_A(novo_A, novo_A[i], -1.0)
        else:
            novo_A = adiciona_valor_A(novo_A, novo_A[i], 0.0)
    return novo_A

def tratamento_sa(dados_arquivo, sinal_index):
    sa = dados_arquivo['sa']
    A = []
    b = []
    c = dados_arquivo['coeficiente']
    sinais = []
    pares_sinais_inversos = {'>=':'<=','<=':'>=','==':'=='}
    for exp in sa:
        b.append(exp[-1] if exp[-1] >= 0 else (exp[-1]*-1))
        A.append(exp[:sinal_index+1] if exp[-1] >= 0 else list(map(lambda x: x*(-1), exp[:sinal_index])))
        sinais.append(exp[sinal_index+1] if exp[-1] >= 0 else pares_sinais_inversos[exp[sinal_index+1]])
    A = forma_canonica(A, sinais)
    return np.array(A), np.array(b), np.array(c)

def gera_combinacoes(qtd_linhas, qtd_colunas):
    valores = [i for i in range(qtd_linhas)]
    combinacoes = permutations(valores)
    lista_combinacoes = []
    for combinacao in combinacoes:
      lista_combinacoes.append(list(combinacao))
    return lista_combinacoes

def gera_matriz_B_R(A, combinacao_colunas):
    A_transposta = A.T
    num_linhas, num_colunas = A.shape
    combinacao_R = list(filter(lambda x: x not in combinacao_colunas, [i for i in range(num_colunas)]))
    matriz_b = np.array([A_transposta[i] for i in combinacao_colunas])
    matriz_r = np.array([A_transposta[i] for i in combinacao_R])
    return np.array(matriz_b.T)

def gera_solucao(B,b):
    B_inversa = np.linalg.inv(np.array(B))
    solucao = np.dot(B_inversa, b)
    return solucao

def buscar_melhor_solucao(solucoes, c):
    resultados = [np.dot(c, solucao) for solucao in solucoes]
    return max(resultados)

def junta(matriz_solucao, num_variaveis, combinacao):
  solucao = []
  for i in range(int(num_variaveis)):
      valor = 0.0
      if i in combinacao:
        index = combinacao.index(i)
        valor = matriz_solucao[index]
      solucao.append(valor)
  return np.array(solucao)

def simplex(dados_arquivo):
    A, b, c = tratamento_sa(dados_arquivo, int(dados_arquivo['meta']['num_var_original']-1))
    qtd_linha_A, qtd_coluna_A = A.shape
    combinacoes = gera_combinacoes(qtd_linha_A, qtd_coluna_A)
    solucoes = []
    for combinacao in combinacoes:
        B, R = gera_matriz_B_R(A, combinacao, qtd_coluna_A)
        print("MATRIZ B")
        print(B)
        print("==============================")
        determinante = np.linalg.det(B)
        if determinante != 0:
            solucoes.append(gera_solucao(B,b))
    return buscar_melhor_solucao(solucoes, c)

if __name__ == '__main__':
    dados_arquivo = le_arquivo('problema_lp\problema1.txt')
    print(simplex(dados_arquivo))