# mpi_gather_criancas.py
# Ideia para entendimento academico
# - Cada criança faz um bloquinho de 10 números iguais ao seu "número da camiseta" (rank).
# - O Líder (rank 0) junta todos os bloquinhos (Gather).
# - No fim, o Líder mostra os bloquinhos por criança e a lista "achatada".

from mpi4py import MPI

TAM_VET = 10
ROOT = 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Cada criança cria seu bloquinho: [rank, rank, ..., rank] (10 vezes)
    vet_envia = [rank] * TAM_VET

    # Gather: o Líder recebe a lista de bloquinhos (um por rank)
    # Nos outros ranks, gathered = None
    gathered = comm.gather(vet_envia, root=ROOT)

    if rank == ROOT:
        print(f"[Líder] Recebi {size} bloquinhos de tamanho {TAM_VET}.\n")

        # Mostrar por criança (processo)
        for r, bloco in enumerate(gathered):
            print(f"Do processo {r}: {bloco}")

        # Versão "achatada" (igual ao vetor único do C)
        vetor_achatado = [num for bloco in gathered for num in bloco]
        print("\nVetor achatado (como no C):")
        print(vetor_achatado)

if __name__ == "__main__":
    main()
