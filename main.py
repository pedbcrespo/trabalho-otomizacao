import funcoes as fc
import os

def clear():
    sistema = os.name
    if sistema == "posix":
        os.system("clear")
    elif sistema == "nt":
        os.system("cls")

def opcao1():
    arquivo = input('nome do arquivo: ')
    return fc.executa(arquivo)

def opcao2():
    arquivo = input('nome do arquivo: ')
    return fc.executa(arquivo)

def opcao3():
    print('Saindo do programa.')
    return None


array_funcao = [opcao1,opcao2, opcao3]
while True:
    clear()
    print("Menu:")
    print("1) Executar o Simplex, mostrando resultados intermediários")
    print("2) Executar o Simplex, mostrando apenas o resultado final")
    print("3) Sair do programa")

    opcao = int(input("Escolha uma opção: ")) -1
    if opcao > len(array_funcao):
        continue
    elif opcao == 2:
        array_funcao[opcao]()
        break
    clear()
    array_funcao[opcao]()