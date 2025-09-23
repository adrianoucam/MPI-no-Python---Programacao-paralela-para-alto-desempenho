# mpi_barreira_criancas.py
# Ideia para uso academico
# - A "barreira" é um portão: ninguém passa até TODO MUNDO chegar.
# - A Crianca 0 chega atrasada (espera Enter); as demais esperam na barreira.
# - Quando todas chegam, o portão abre ao mesmo tempo (Barrier).

from mpi4py import MPI
import sys
import time

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()   # quem sou eu?
    size = comm.Get_size()   # quantas criancas?

    if rank == 0:
        print("[Crianca 0] Estou atrasada para a barreira! (segurando o portão) ")
        sys.stdout.flush()
        # Tentamos pedir Enter; se não houver stdin (ambiente nao interativo), fazemos um pequeno atraso.
        try:
            input("Pressione Enter para eu chegar (ou aguarde 3s)... ")
        except (EOFError, KeyboardInterrupt):
            time.sleep(3.0)
    else:
        print(f"[Crianca {rank}] Cheguei na barreira e estou esperando a Crianca 0...")
        sys.stdout.flush()

    # 🔒 BARREIRA: todo mundo para aqui até TODOS chegarem
    comm.Barrier()

    # Após a barreira, todos passam juntos
    print(f"[Crianca {rank}] Passei da barreira! Sou {rank} de {size}.")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
