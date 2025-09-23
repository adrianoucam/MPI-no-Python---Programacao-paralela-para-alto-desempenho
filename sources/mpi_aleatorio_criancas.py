# mpi_aleatorio_criancas.py
# - Rank 0 escolhe uma quantidade aleatória de "bolinhas" (números) e envia ao Rank 1.
# - Rank 1 recebe até MAX bolinhas e usa o status para saber quantas vieram,
#   quem enviou (source) e qual etiqueta (tag) foi usada.
# - Usamos MPI.ANY_SOURCE e MPI.ANY_TAG no Recv, como no código C.

from mpi4py import MPI
import numpy as np
import random

MAX = 100
ORIGEM = 0
DESTINO = 1
TAG = 42  # etiqueta (tag) só para identificarmos a mensagem

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 2:
        if rank == 0:
            print("Por favor, execute com pelo menos 2 processos, ex.: mpiexec -n 2 python mpi_aleatorio_criancas.py")
        return

    if rank == ORIGEM:
        # Semente pseudo-aleatória baseada no relógio do MPI (varia a cada execução)
        random.seed(int(MPI.Wtime() * 1e6) + rank)

        # Quantas bolinhas? um número entre 0 e MAX
        total_num = random.randint(0, MAX)

        # Conteúdo das bolinhas: aqui vamos mandar 1..total_num (didático)
        numeros = np.arange(1, total_num + 1, dtype=np.int32)

        # Envia exatamente total_num inteiros (se for 0, envia mensagem vazia)
        # Destino fixo = Rank 1, Tag = TAG
        comm.Send([numeros, MPI.INT], dest=DESTINO, tag=TAG)
        print(f"[Rank {rank}] Enviei {total_num} numero(s) para o Rank {DESTINO} (tag={TAG}).")

    elif rank == DESTINO:
        # Buffer com capacidade para ATÉ MAX inteiros
        buffer = np.empty(MAX, dtype=np.int32)

        # Recebe de QUALQUER origem/etiqueta (ANY_SOURCE / ANY_TAG)
        status = MPI.Status()
        comm.Recv([buffer, MPI.INT], source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)

        # Quantos inteiros realmente chegaram?
        recebidos = status.Get_count(MPI.INT)
        origem = status.Get_source()
        tag = status.Get_tag()

        # Pegamos só a parte preenchida
        dados = buffer[:recebidos]

        print(f"[Rank {rank}] Recebi {recebidos} numero(s). Origem = {origem}, tag = {tag}.")
        if recebidos > 0:
            # Mostra alguns valores (ou todos, se forem poucos)
            mostrar = dados.tolist() if recebidos <= 20 else dados[:20].tolist() + ["..."]
            print(f"[Rank {rank}] Valores: {mostrar}")
        else:
            print(f"[Rank {rank}] Nenhum numero recebido desta vez (mensagem vazia).")

    else:
        # Outros processos (se houver) apenas observam
        print(f"[Rank {rank}] Sem papel nesta brincadeira.")

if __name__ == "__main__":
    main()
