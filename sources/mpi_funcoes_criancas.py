# mpi_funcoes_criancas.py
# Ideia: mostrar a "identidade do time" MPI
# - Versão do MPI (uniforme)
# - Quantas jogadoras (num_procs) e quem eu sou (rank)
# - Em qual "quadra" (nome do computador) estou jogando
# - Tempo gasto e precisão do relógio do "juiz" (Wtick)

# mpi_funcoes_criancas.py
from mpi4py import MPI
import sys

def main():
    # (Opcional) inicializa explicitamente
    if not MPI.Is_initialized():
        MPI.Init()

    t0 = MPI.Wtime()

    versao, subversao = MPI.Get_version()
    print(f"Versao do MPI = {versao} Subversao = {subversao}")

    comm = MPI.COMM_WORLD
    num_procs = comm.Get_size()     # OK em mpi4py
    meu_ranque = comm.Get_rank()    # <- aqui é Get_rank(), não Get_Rank()
    maquina = MPI.Get_processor_name()

    print(f"Numero de tarefas = {num_procs}  Meu ranque = {meu_ranque}  Executando em {maquina}")

    t1 = MPI.Wtime()
    precisao = MPI.Wtick()
    print(f"Foram gastos {t1 - t0:0.6f} segundos com precisao de {precisao:0.3e} segundos")

    # (Opcional) barreira só para organizar a saída
    comm.Barrier()
    MPI.Finalize()

if __name__ == "__main__":
    main()
