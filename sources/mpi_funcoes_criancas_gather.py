# mpi_funcoes_criancas_gather.py
from mpi4py import MPI

def main():
    # (Opcional) inicializa explicitamente
    if not MPI.Is_initialized():
        MPI.Init()

    t0 = MPI.Wtime()
    versao, subversao = MPI.Get_version()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    maquina = MPI.Get_processor_name()
    precisao = MPI.Wtick()
    t1 = MPI.Wtime()
    decorrido = t1 - t0

    # Cada processo prepara seu “cartão de identidade”
    info = {
        "rank": rank,
        "size": size,
        "maquina": maquina,
        "versao": versao,
        "subversao": subversao,
        "tempo": decorrido,
        "wtick": precisao,
    }

    # Root junta tudo
    todos = comm.gather(info, root=0)

    if rank == 0:
        # Ordena por rank e imprime
        todos.sort(key=lambda x: x["rank"])
        v, sv = versao, subversao
        print(f"Versao do MPI = {v}  Subversao = {sv}\n")
        print("Resumo dos processos (ordenado por rank):")
        print("rank | size | maquina                      | tempo (s) | Wtick (s)")
        print("-----+------+-------------------------------+-----------+----------")
        for d in todos:
            print(f"{d['rank']:>4} | {d['size']:>4} | {d['maquina']:<29} | "
                  f"{d['tempo']:>9.6f} | {d['wtick']:.3e}")

    comm.Barrier()
    MPI.Finalize()

if __name__ == "__main__":
    main()
