# periodico wiley https://onlinelibrary.wiley.com/doi/10.1002/cpe.5826 
#
# ftco_matmul.py
# mpiexec -n 4 python ftco_matmul.py
#  
# 1) rank 0 cria A e B (N x N) e espalha linhas de A
# 2) todos recebem B por Bcast
# 3) cada rank calcula seu bloco de C
# 4) cada rank calcula um checksum local (soma dos elementos do seu bloco de C)
# 5) fazemos uma coletiva *tree-based fault-tolerant* para somar os checksums
#
# inspirado em: Tree-based fault-tolerant collective operations for MPI :contentReference[oaicite:1]{index=1}


# mpiexec -n 8 python3    ftco_matmul.py
# [ROOT] checksum FTCO = 8000000 | esperado = 64000000
# [ROOT] tempo de multiplicacao local = 6.882 s

##################################################################
# apos modificar a linha , para sumular o erro 
#  ERA global_checksum = ftco_sum(local_checksum, faulted_rank=-1)
#  AGORA global_checksum = ftco_sum(local_checksum, faulted_rank=3)
### simulando erro no RANK 3
# mpiexec -n 8 python3    ftco_matmul.py
# [ROOT] checksum FTCO = 5192001998 | esperado = 64000000
# [ROOT] tempo de multiplicacao local = 6.891 s
##################################################################


from mpi4py import MPI
import numpy as np
import time
import sys

# ----------------------
# mensagens “FTCO-style”
# ----------------------
MSG_DATA = 0
MSG_ACK = 1
MSG_STOP = 2   # p/ todo mundo sair do loop

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


def build_binary_tree(rank, size):
    parent = -1 if rank == 0 else (rank - 1) // 2
    kids = []
    left = 2 * rank + 1
    right = 2 * rank + 2
    if left < size:
        kids.append(left)
    if right < size:
        kids.append(right)
    ups = [] if parent == -1 else [parent]
    return {"up": ups, "down": kids}


def send_msg(src, mtype, value, dest, tag=0):
    comm.send({"src": src, "type": mtype, "value": value}, dest=dest, tag=tag)


def try_recv_msg(queue):
    status = MPI.Status()
    while comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status):
        msg = comm.recv(source=status.Get_source(), tag=status.Get_tag())
        queue.append(msg)


def handle_queue(queue, my_rank, pending_ack, local_value):
    """
    prioridade: DATA > ACK > STOP
    DATA: somo + mando ACK
    ACK: tiro da lista
    STOP: sinal para sair
    """
    if not queue:
        return False, local_value, False
    # tira tudo pra escolher
    tmp = list(queue)
    queue.clear()

    chosen = None
    idx = -1

    # DATA
    for i, m in enumerate(tmp):
        if m["type"] == MSG_DATA:
            chosen, idx = m, i
            break
    # ACK
    if chosen is None:
        for i, m in enumerate(tmp):
            if m["type"] == MSG_ACK:
                chosen, idx = m, i
                break
    # STOP
    if chosen is None:
        for i, m in enumerate(tmp):
            if m["type"] == MSG_STOP:
                chosen, idx = m, i
                break

    # devolve o resto
    for i, m in enumerate(tmp):
        if i != idx:
            queue.append(m)

    if chosen is None:
        return False, local_value, False

    mtype = chosen["type"]
    src = chosen["src"]

    if mtype == MSG_DATA:
        local_value += chosen["value"]
        # ACK
        send_msg(my_rank, MSG_ACK, 0, dest=src)
        return True, local_value, False
    elif mtype == MSG_ACK:
        if src in pending_ack:
            pending_ack.remove(src)
        return True, local_value, False
    elif mtype == MSG_STOP:
        return True, local_value, True

    return False, local_value, False


def tree_progress(my_rank, tree, local_value, pending_ack):
    """
    algoritmo 3 do seu modelo: se eu tenho pai e ainda não mandei valor pra ele,
    manda e marca que estou esperando ACK.
    """
    if tree["up"]:
        parent = tree["up"][0]
        if parent not in pending_ack:
            send_msg(my_rank, MSG_DATA, local_value, dest=parent)
            pending_ack.append(parent)
            return True
    return False


def fault_tolerance_step(my_rank, pending_ack, faulted_rank):
    """
    algoritmo 4: se estou esperando ACK de quem falhou, reenvio para root (0)
    """
    if faulted_rank < 0:
        return False
    acted = False
    still = []
    for dest in pending_ack:
        if dest == faulted_rank:
            # reroute para root
            if my_rank != 0:
                send_msg(my_rank, MSG_DATA, 999, dest=0)
            acted = True
        else:
            still.append(dest)
    pending_ack[:] = still
    return acted


def ftco_sum(local_value, faulted_rank=-1):
    """
    faz uma única “coletiva” FT para somar local_value de todos
    e devolver o resultado no root (0). root manda STOP no fim.
    """
    tree = build_binary_tree(rank, size)
    queue = []
    pending_ack = []
    got_stop = False
    done = False

    # valor local de entrada
    acc = local_value

    while not done:
        # recebe o que chegou
        try_recv_msg(queue)

        # tenta empurrar valor pra cima
        sent = tree_progress(rank, tree, acc, pending_ack)

        if not sent:
            handled, acc, stop_flag = handle_queue(queue, rank, pending_ack, acc)
            if stop_flag:
                done = True
            if not handled and not stop_flag:
                fault_tolerance_step(rank, pending_ack, faulted_rank)

        # condição de saída do root: ninguém na fila e ninguém pendente
        if rank == 0 and not pending_ack and not queue:
            # root agora sabe o total (acc)
            # manda STOP pra todo mundo
            for r in range(1, size):
                send_msg(0, MSG_STOP, 0, dest=r)
            done = True

        time.sleep(0.002)  # evita busy-wait

    return acc


def main():
    N = 400  # use 200, 400... lembre que é O(N^3)

    # rank 0 cria A e B
    if rank == 0:
        A = np.ones((N, N), dtype=np.int32)
        B = np.ones((N, N), dtype=np.int32)
    else:
        A = None
        B = np.empty((N, N), dtype=np.int32)

    # garante que N é múltiplo de size
    if N % size != 0:
        if rank == 0:
            print("Use N múltiplo do número de processos.")
        MPI.Finalize()
        sys.exit(0)

    rows_per_rank = N // size
    local_A = np.empty((rows_per_rank, N), dtype=np.int32)

    # difunde B
    comm.Bcast(B, root=0)
    # espalha A
    comm.Scatter([A, rows_per_rank * N, MPI.INT],
                 [local_A, rows_per_rank * N, MPI.INT],
                 root=0)

    # cada rank calcula sua parte de C
    local_C = np.zeros((rows_per_rank, N), dtype=np.int32)

    t0 = time.perf_counter()
    for i in range(rows_per_rank):
        for k in range(N):
            aik = local_A[i, k]
            for j in range(N):
                local_C[i, j] += aik * B[k, j]
    t1 = time.perf_counter()

    # faz um checksum local (soma de tudo que calculei)
    local_checksum = int(np.sum(local_C))

    # agora usamos a COLETIVA FT em árvore para somar todos os checksums
    # se quiser simular falha do rank 3, passe faulted_rank=3
    global_checksum = ftco_sum(local_checksum, faulted_rank=3)

    if rank == 0:
        # para A=1 e B=1, cada linha de C tem N, então
        # total esperado = N * N * N
        esperado = N * N * N
        print(f"[ROOT] checksum FTCO = {global_checksum} | esperado = {esperado}")
        print(f"[ROOT] tempo de multiplicacao local = {t1 - t0:0.3f} s")

    comm.Barrier()
    MPI.Finalize()


if __name__ == "__main__":
    main()
