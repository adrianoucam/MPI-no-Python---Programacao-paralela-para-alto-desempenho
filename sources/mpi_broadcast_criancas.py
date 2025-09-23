# mpi_broadcast_criancas.py
# Ideia para uso academico:
# - A Crianca 0 é o "Líder": ela escolhe (ou digita) um número.
# - Com o broadcast, o número do Líder é falado para TODAS as criancas de uma só vez.
# - No final, todas as criancas mostram que receberam o MESMO número.

from mpi4py import MPI

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()   # quem sou eu?
    size = comm.Get_size()   # quantas criancas?
    root = 0                 # o "Lider" é a Crianca 0

    # Cada crianca comeca com um valor diferente (só para comparacão):
    valor = rank

    if rank == root:
        # O Lider pede um número (se não houver teclado, usa um padrão)
        try:
            print("[Lider] Entre um valor inteiro:", flush=True)
            txt = input()
            valor = int(txt)
        except Exception:
            valor = 42
            print("[Líder] Sem entrada válida; usando o valor padrão 42.", flush=True)

    # 📨 Broadcast: o Líder fala e todo mundo recebe o mesmo valor
    # Em mpi4py, a forma simples é usar objetos Python:
    valor = comm.bcast(valor if rank == root else None, root=root)

    # Agora todas as criancas têm o mesmo valor
    print(f"[Crianca {rank}] Recebi o valor do Lider: {valor}")

if __name__ == "__main__":
    main()
