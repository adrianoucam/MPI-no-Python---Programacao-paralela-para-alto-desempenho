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


# mpiexec -n 4 python3 ftco_matmul.py
# [ROOT] checksum FTCO = 64000000 | esperado = 64000000
# [ROOT] tempo de multiplicacao local = 11.435 s

#  apos alteracao : global_checksum = ftco_reduce_sum(local_checksum, faulted_rank=3)
# mpiexec -n 4 python3 ftco_matmul.py
# [ROOT] checksum FTCO = 48000000 | esperado = 64000000
# [ROOT] tempo de multiplicacao local = 11.361 s

# O ALGORITMO EXECUTOU TODAS AS OPERACOES , EXCETO DO RANK 3 
##################################################################
# apos modificar a linha , para sumular o erro 
#  ERA global_checksum = ftco_reduce_sum(local_checksum, faulted_rank=-1)
#  AGORA global_checksum = ftco_reduce_sum(local_checksum, faulted_rank=3)
### simulando erro no RANK 3
# mpiexec -n 8 python3    ftco_matmul.py
# [ROOT] checksum FTCO = 5192001998 | esperado = 64000000
# [ROOT] tempo de multiplicacao local = 6.891 s
##################################################################


from mpi4py import MPI
import numpy as np
import time
import sys



MSG_DATA = 0
MSG_ACK  = 1
MSG_STOP = 2

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


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
    children = []
    l = 2 * rank + 1
    r = 2 * rank + 2
    if l < size:
        children.append(l)
    if r < size:
        children.append(r)
    return parent, children


def send_msg(src, mtype, value, dest):
    comm.send({"src": src, "type": mtype, "value": value}, dest=dest)




def try_recv(queue):
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

def ftco_reduce_sum(local_value, faulted_rank=-1):
    """
    Redução em árvore tolerante a falhas:
    - cada processo espera o valor de TODOS os filhos (cada filho conta uma vez)
    - só então manda UM valor pro pai
    - o root manda STOP no final
    """
    parent, children = build_binary_tree(rank, size)

    # quem ainda não entregou o valor desta redução
    waiting_children = set(children)
    # para evitar somar 2x o mesmo filho
    received_from = set()

    acc = local_value
    waiting_ack_from_parent = (parent != -1)
    done = False

    while not done:
        # recebe tudo que chegou
        status = MPI.Status()
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status):
            msg = comm.recv(source=status.Get_source(), tag=status.Get_tag())
            mtype = msg["type"]
            src   = msg["src"]
            val   = msg["value"]

            if mtype == MSG_DATA:
                # só soma se ainda não somamos desse filho
                if src not in received_from:
                    acc += val
                    received_from.add(src)
                    if src in waiting_children:
                        waiting_children.remove(src)
                # de qualquer forma manda ACK
                send_msg(rank, MSG_ACK, 0, dest=src)

            elif mtype == MSG_ACK:
                # pai confirmou; podemos parar de esperar
                if src == parent:
                    waiting_ack_from_parent = False

            elif mtype == MSG_STOP:
                done = True

        # tolerância simples: se um filho falhou, paramos de esperar por ele
        if faulted_rank in waiting_children:
            waiting_children.remove(faulted_rank)

        # se não sou root e já recebi de todos os filhos e ainda não mandei pro pai:
        if parent != -1 and not waiting_children and waiting_ack_from_parent:
            send_msg(rank, MSG_DATA, acc, dest=parent)
            # agora esperamos o ACK

        # se sou root: quando não tiver mais filhos pra esperar e não houver mensagens pendentes, termino
        if rank == 0 and not waiting_children:
            # root conhece o valor final
            # manda STOP pra todo mundo
            for p in range(1, size):
                send_msg(0, MSG_STOP, 0, dest=p)
            done = True

        time.sleep(0.001)

    return acc



def ftco_reduce_sum2(local_value, faulted_rank=-1):
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
    global_checksum = ftco_reduce_sum(local_checksum, faulted_rank=3)

    if rank == 0:
        esperado = N * N * N
        print(f"[ROOT] checksum FTCO = {global_checksum} | esperado = {esperado}")
        # para A=1 e B=1, cada linha de C tem N, então
        # total esperado = N * N * N      
       
        print(f"[ROOT] tempo de multiplicacao local = {t1 - t0:0.3f} s")

    comm.Barrier()
    MPI.Finalize()


if __name__ == "__main__":
    main()
