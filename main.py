def separa_numeros(linha):
    lista = []
    for val in linha.split():
        try:
            val = float(val.replace(',','.')) if ',' in val else float(val)
        except:
            pass
        lista += [val]
    return lista

def gera_dicionario_dados(lista_chaves, linha):
    nums = separa_numeros(linha)
    dicionario_resposta = {}
    for i in range(len(nums)):
        dicionario_resposta[lista_chaves[i]] = nums[i]
    return dicionario_resposta

def le_arquivo(nome_arquivo):
    eh_solucao = False
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
        for linha in linhas:
            if eh_solucao:
                dicionario_arquivo['solucao'] = separa_numeros(linha)
                eh_solucao = False
            if '//' in linha:
                eh_solucao = True
                continue
        return dicionario_arquivo

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

def tratamento_sa(sa, sinal_index):
    A = []
    b = []
    sinais = []
    for exp in sa:       
        A.append(exp[:sinal_index])
        b.append(exp[-1])
        sinais.append(exp[sinal_index+1])
    return forma_canonica(A, sinais), b


def simplex(tableau):
    pass

def main():
    while True:
        print("Menu:")
        print("1) Executar o Simplex, mostrando resultados intermediários")
        print("2) Executar o Simplex, mostrando apenas o resultado final")
        print("3) Sair do programa")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            nome_arquivo = input("Digite o nome do arquivo: ")
            tableau, outras_informacoes = le_arquivo(nome_arquivo)
            
            print("Tableau Inicial:")
            print(tableau)
            
            executar_simplex = input("Iniciar execução do Simplex? (S/N): ")
            
            if executar_simplex.lower() == "s":
                resultado = simplex(tableau)
            else:
                continue
        
        elif opcao == "2":
            nome_arquivo = input("Digite o nome do arquivo: ")
            tableau, outras_informacoes = le_arquivo(nome_arquivo)
            
            resultado = simplex(tableau)
            
            if resultado == "otima":
                print("Solução ótima encontrada:")
            elif resultado == "inviavel":
                print("Problema inviável")
            elif resultado == "ilimitado":
                print("Problema ilimitado")
        
        elif opcao == "3":
            print("Encerrando o programa.")
            break
        
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    # main()
    dados_arquivo = le_arquivo('problema1.txt')
    A, b = tratamento_sa(dados_arquivo['sa'], int(dados_arquivo['meta']['num_var_original']-1))
    print(A, b)
