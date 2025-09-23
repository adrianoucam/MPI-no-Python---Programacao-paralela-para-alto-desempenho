# mpi_bolinhas.py
# Versão "academica para entendimento" do exemplo MPI:
# - Rank 0 escolhe uma quantidade ALEATÓRIA de números (bolinhas) e envia para o Rank 1
# - Rank 1 recebe até MAX bolinhas e usa o "status" para saber QUANTAS realmente chegaram

from mpi4py import MPI
import numpy as np
import random

MAX = 100            # capacidade máxima da "sacolinha" do receptor
ORIGEM = 0
DESTINO = 1
TAG = 0              # etiqueta da mensagem (como um adesivo no pacote)

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Precisamos de pelo menos 2 processos (duas crianças)
    if size < 2:
        if rank == 0:
            print("Por favor, execute com pelo menos 2 processos (ex.: mpiexec -n 2 python mpi_bolinhas.py)")
        return

    if rank == ORIGEM:
        # Criança 0: escolhe quantas bolinhas vai enviar
        # Usamos uma semente variável para deixar o aleatório diferente a cada execução
        random.seed(int(MPI.Wtime() * 1e6) + rank)

        # Quantas bolinhas? um número entre 0 e MAX (inclusive)
        total_num = random.randint(0, MAX)

        # Quais bolinhas? aqui colocamos números simples: 1, 2, 3, ..., total_num
        # (poderiam ser números aleatórios também)
        bolinhas = np.arange(1, total_num + 1, dtype=np.int32)

        # Envia as bolinhas (todas de uma vez) para o DESTINO
        # Observação: enviamos só "total_num" bolinhas; o receptor tem espaço para até MAX
        if total_num > 0:
            comm.Send([bolinhas, MPI.INT], dest=DESTINO, tag=TAG)
        else:
            # Se total_num == 0, não há nada para enviar; ainda assim avisamos com uma mensagem vazia
            vazio = np.empty(0, dtype=np.int32)
            comm.Send([vazio, MPI.INT], dest=DESTINO, tag=TAG)

        print(f"[Rank {rank}] Enviei {total_num} bolinha(s) para o Rank {DESTINO}.")
    
    elif rank == DESTINO:
        # Criança 1: prepara a sacolinha para receber ATÉ MAX bolinhas
        sacolinha = np.empty(MAX, dtype=np.int32)

        # Recebe do ORIGEM, qualquer quantidade até MAX
        status = MPI.Status()
        comm.Recv([sacolinha, MPI.INT], source=ORIGEM, tag=TAG, status=status)

        # Descobre QUANTAS bolinhas realmente chegaram usando o "status"
        qtd_recebida = status.Get_count(MPI.INT)

        # Pegamos só a parte preenchida da sacolinha
        recebidas = sacolinha[:qtd_recebida]

        print(
            f"[Rank {rank}] Recebi {qtd_recebida} bolinha(s). "
            f"De quem? Rank {status.Get_source()} | Etiqueta: {status.Get_tag()}"
        )
        if qtd_recebida > 0:
            print(f"[Rank {rank}] As bolinhas são: {recebidas.tolist()}")
        else:
            print(f"[Rank {rank}] A sacolinha veio vazia desta vez 😅")

    else:
        # Outras crianças (se existirem) ficam só observando
        print(f"[Rank {rank}] Estou só observando a troca de bolinhas.")

if __name__ == "__main__":
    main()
