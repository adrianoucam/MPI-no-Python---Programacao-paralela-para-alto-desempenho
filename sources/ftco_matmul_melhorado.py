# ftco_matmul_melhorado.py
from mpi4py import MPI
import numpy as np
import time

TAG_WORK = 10
TAG_RESULT = 11
TAG_STOP = 12

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


def make_matrices(N):
    A = np.ones((N, N), dtype=np.int32)
    B = np.ones((N, N), dtype=np.int32)
    return A, B


def master(N=1000, block_rows=50, timeout=2.0):
    A, B = make_matrices(N)
    comm.bcast(B, root=0)

    # monta os blocos de linhas
    blocks = []
    blk_id = 0
    for rs in range(0, N, block_rows):
        re = min(rs + block_rows, N)
        blocks.append({
            "id": blk_id,
            "row_start": rs,
            "row_end": re,
            "assigned_to": None,
            "assigned_at": None,
            "done": False,
            "checksum": 0,
        })
        blk_id += 1

    workers = list(range(1, size))
    free_workers = workers[:]

    t0 = time.time()

    while True:
        # 1) atribuir blocos que ainda não foram feitos
        for blk in blocks:
            if blk["done"]:
                continue
            if blk["assigned_to"] is None and free_workers:
                w = free_workers.pop(0)
                payload = (
                    blk["id"],
                    blk["row_start"],
                    blk["row_end"],
                    A[blk["row_start"]:blk["row_end"], :],
                )
                comm.send(payload, dest=w, tag=TAG_WORK)
                blk["assigned_to"] = w
                blk["assigned_at"] = time.time()

        # 2) checar timeout e reatribuir
        now = time.time()
        for blk in blocks:
            if blk["done"]:
                continue
            if blk["assigned_to"] is not None:
                if now - blk["assigned_at"] > timeout:
                    print(f"[MASTER] timeout no bloco {blk['id']} do worker {blk['assigned_to']}, reatribuindo", flush=True)
                    blk["assigned_to"] = None
                    blk["assigned_at"] = None
                    # não devolvemos o worker “lento” pra lista

        # 3) colher resultados
        status = MPI.Status()
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=TAG_RESULT, status=status):
            data = comm.recv(source=status.Get_source(), tag=TAG_RESULT, status=status)
            w = status.Get_source()
            blk_id, checksum = data
            blk = blocks[blk_id]
            blk["done"] = True
            blk["checksum"] = checksum
            blk["assigned_to"] = None
            blk["assigned_at"] = None
            # esse worker voltou a ser saudável
            if w not in free_workers:
                free_workers.append(w)

        # 4) terminou?
        if all(b["done"] for b in blocks):
            break

        time.sleep(0.01)

    # manda STOP pra todo mundo
    for w in workers:
        comm.send(None, dest=w, tag=TAG_STOP)

    total_checksum = sum(b["checksum"] for b in blocks)
    esperado = N * N * N
    t1 = time.time()
    print(f"[MASTER] checksum final = {total_checksum} | esperado = {esperado}")
    print(f"[MASTER] tempo total = {t1 - t0:0.3f}s")


def workerold():
    B = comm.bcast(None, root=0)

    while True:
        status = MPI.Status()
        comm.probe(source=0, tag=MPI.ANY_TAG, status=status)
        tag = status.Get_tag()
        if tag == TAG_STOP:
            comm.recv(source=0, tag=TAG_STOP)
            break

        blk_id, rs, re, Ablk = comm.recv(source=0, tag=TAG_WORK)

        # --------- SIMULAÇÃO DE FALHA AQUI ----------
        # rank 3 recebe o bloco 0 e nunca responde
        if rank == 3 : # and blk_id == 0:
            print(f"[WORKER {rank}] simulando falha no bloco {blk_id} (vou travar)", flush=True)
            # “caiu”: nunca devolve o resultado
            time.sleep(9999)
            # não chega aqui
        # --------------------------------------------

        Cblk = Ablk.dot(B)
        checksum = int(np.sum(Cblk))
        comm.send((blk_id, checksum), dest=0, tag=TAG_RESULT)


def worker():
    B = comm.bcast(None, root=0)

    while True:
        status = MPI.Status()
        comm.probe(source=0, tag=MPI.ANY_TAG, status=status)
        tag = status.Get_tag()

        if tag == TAG_STOP:
            comm.recv(source=0, tag=TAG_STOP)
            break

        blk_id, rs, re, Ablk = comm.recv(source=0, tag=TAG_WORK)

        # --------- SIMULAÇÃO DE FALHA CONTROLADA ----------
        if rank == 3 : # and blk_id == 0:
            print(f"[WORKER {rank}] simulando falha no bloco {blk_id} (vou ficar lento)", flush=True)
            # em vez de dormir 9999s, dorme em pedaços e verifica STOP
            while True:
                # vê se o mestre já pediu pra parar
                if comm.Iprobe(source=0, tag=TAG_STOP):
                    comm.recv(source=0, tag=TAG_STOP)
                    return
                time.sleep(0.5)   # continua “travado/lento”
            # (não chega aqui)
        # --------------------------------------------------

        # trabalho normal
        Cblk = Ablk.dot(B)
        checksum = int(np.sum(Cblk))
        comm.send((blk_id, checksum), dest=0, tag=TAG_RESULT)

def main():
    if size < 2:
        if rank == 0:
            print("Precisa de pelo menos 2 processos.")
        return

    if rank == 0:
        master(N=1000, block_rows=50, timeout=2.0)
    else:
        worker()


if __name__ == "__main__":
    main()
