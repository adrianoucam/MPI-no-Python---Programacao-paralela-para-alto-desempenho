from mpi4py import MPI
import sys
import time
from collections import deque

# tipos de mensagem
MSG_DATA = 0
MSG_KEEPALIVE = 1
MSG_ACK = 2
MSG_STOP = 3  # <- novo

def build_binary_tree(rank, size):
    parent = -1 if rank == 0 else (rank - 1) // 2
    down = []
    left = 2 * rank + 1
    right = 2 * rank + 2
    if left < size:
        down.append(left)
    if right < size:
        down.append(right)
    up = []
    if parent >= 0:
        up.append(parent)
    return {"up": up, "down": down}

def send_msg(comm, src_rank, msg_type, value, dest, tag=0):
    comm.send({"src": src_rank, "type": msg_type, "value": value}, dest=dest, tag=tag)

def try_recv_msg(comm, queue):
    status = MPI.Status()
    got = False
    while comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status):
        m = comm.recv(source=status.Get_source(), tag=status.Get_tag())
        queue.append(m)
        got = True
    return got

def handle_message_queue(queue, my_rank, comm, local_value, pending_ack):
    if not queue:
        return False, local_value, False  # handled?, value, got_stop?

    temp = list(queue)
    queue.clear()

    chosen = None
    chosen_idx = -1

    # prioridade DATA
    for i, m in enumerate(temp):
        if m["type"] == MSG_DATA:
            chosen = m
            chosen_idx = i
            break
    # prioridade KEEPALIVE
    if chosen is None:
        for i, m in enumerate(temp):
            if m["type"] == MSG_KEEPALIVE:
                chosen = m
                chosen_idx = i
                break
    # prioridade ACK
    if chosen is None:
        for i, m in enumerate(temp):
            if m["type"] == MSG_ACK:
                chosen = m
                chosen_idx = i
                break
    # prioridade STOP (se chegou)
    if chosen is None:
        for i, m in enumerate(temp):
            if m["type"] == MSG_STOP:
                chosen = m
                chosen_idx = i
                break

    for i, m in enumerate(temp):
        if i != chosen_idx:
            queue.append(m)

    if chosen is None:
        return False, local_value, False

    mtype = chosen["type"]
    src = chosen["src"]

    if mtype == MSG_DATA:
        local_value += chosen["value"]
        send_msg(comm, my_rank, MSG_ACK, 0, dest=src)
        return True, local_value, False
    elif mtype == MSG_KEEPALIVE:
        send_msg(comm, my_rank, MSG_ACK, 0, dest=src)
        return True, local_value, False
    elif mtype == MSG_ACK:
        if src in pending_ack:
            pending_ack[:] = [p for p in pending_ack if p != src]
        return True, local_value, False
    elif mtype == MSG_STOP:
        # chegou ordem de parar
        return True, local_value, True

    return False, local_value, False

def tree_progress_allreduce(my_rank, comm, ni, local_value, pending_ack):
    if ni["up"]:
        parent = ni["up"][0]
        if parent not in pending_ack:
            send_msg(comm, my_rank, MSG_DATA, local_value, dest=parent)
            pending_ack.append(parent)
            return True
    return False

def fault_tolerance_step(my_rank, comm, pending_ack, faulted_rank):
    if faulted_rank < 0:
        return False
    acted = False
    new_p = []
    for dest in pending_ack:
        if dest == faulted_rank:
            if my_rank != 0:
                send_msg(comm, my_rank, MSG_DATA, 999, dest=0)
            acted = True
        else:
            new_p.append(dest)
    pending_ack[:] = new_p
    return acted

def pre_collective_functionality(delay_ms, my_rank, comm, local_value, queue, pending_ack):
    t0 = time.time()
    while (time.time() - t0) * 1000.0 < delay_ms:
        try_recv_msg(comm, queue)
        if queue:
            m = queue.popleft()
            if m["type"] in (MSG_KEEPALIVE, MSG_DATA):
                if m["type"] == MSG_DATA:
                    local_value += m["value"]
                send_msg(comm, my_rank, MSG_ACK, 0, dest=m["src"])
        time.sleep(0.01)
    return local_value

def ftco_collective_main(my_rank, size, initial_value, faulted_rank, use_pre_delay):
    comm = MPI.COMM_WORLD
    ni = build_binary_tree(my_rank, size)
    local_value = initial_value
    queue = deque()
    pending_ack = []

    if use_pre_delay and my_rank == 2:
        local_value = pre_collective_functionality(1500, my_rank, comm,
                                                   local_value, queue, pending_ack)

    done = False
    iterations = 0
    got_stop = False

    while not done and iterations < 4000:
        iterations += 1
        try_recv_msg(comm, queue)

        if not got_stop:
            sent = tree_progress_allreduce(my_rank, comm, ni, local_value, pending_ack)
        else:
            sent = False

        if not sent:
            handled, local_value, got_stop_msg = handle_message_queue(
                queue, my_rank, comm, local_value, pending_ack
            )
            if got_stop_msg:
                got_stop = True
            if not handled and not got_stop:
                fault_tolerance_step(my_rank, comm, pending_ack, faulted_rank)

        # ROOT decide quando acabou e avisa todo mundo
        if my_rank == 0 and not pending_ack and not queue:
            # manda STOP pra todos
            for r in range(1, size):
                send_msg(comm, 0, MSG_STOP, 0, dest=r)
            done = True

        # os outros saem quando receberam STOP
        if my_rank != 0 and got_stop:
            done = True

        time.sleep(0.005)

    print(f"Rank {my_rank} terminou com valor = {local_value}", flush=True)

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if len(sys.argv) < 2:
        if rank == 0:
            print(f"Uso: mpiexec -n <p> python {sys.argv[0]} <modo(1-5)>")
        MPI.Finalize()
        return

    mode = int(sys.argv[1])
    initial_value = rank

    if mode == 1:
        ftco_collective_main(rank, size, initial_value, faulted_rank=3, use_pre_delay=False)
    elif mode == 5:
        ftco_collective_main(rank, size, initial_value, faulted_rank=-1, use_pre_delay=True)
    else:
        # para não alongar: manteríamos os outros modos como no anterior
        ftco_collective_main(rank, size, initial_value, faulted_rank=-1, use_pre_delay=False)

    comm.Barrier()
    MPI.Finalize()

if __name__ == "__main__":
    main()
