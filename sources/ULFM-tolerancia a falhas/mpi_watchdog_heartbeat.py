# mpi_watchdog_rr.py
# Request–Reply + Heartbeats + Logs por host (tolerante a falhas por timeout)
# Execute com:  mpiexec -n 8 python3 mpi_watchdog_rr.py --n-tasks 40 --task-ms 200 --timeout 2.5

from mpi4py import MPI
import time
import argparse
from collections import deque

# ---- Constantes de protocolo ----
TAG_REQ, TAG_CMD, TAG_RES, TAG_HB = 10, 11, 12, 13
CMD_WORK, CMD_STOP = 1, 2

# ---- Ambiente MPI / Log ----
comm = MPI.COMM_WORLD
RANK = comm.Get_rank()
HOST = MPI.Get_processor_name()

def log(msg: str):
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    ms = int((time.time() % 1) * 1000)
    print(f"[{t}.{ms:03d}] [rank {RANK}] [host {HOST}] {msg}", flush=True)

def now() -> float:
    return MPI.Wtime()

# ---- MASTER ----
def master(comm: MPI.Comm, n_tasks: int, task_ms: int, timeout: float):
    size = comm.Get_size()
    workers = list(range(1, size))
    status = MPI.Status()

    # fila de tarefas pendentes e estado
    pending = deque(range(n_tasks))
    in_flight = {}               # rank -> (task_id, start_time)
    last_hb = {r: now() for r in workers}
    host_by_rank = {}            # rank -> hostname
    done = 0
    t0 = now()

    log(f"MASTER iniciado | tasks={n_tasks} | timeout={timeout}s")

    while done < n_tasks or in_flight:
        # 1) Processa quaisquer mensagens disponíveis (HB, REQ, RES)
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG):
            data = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            src, tag = status.Get_source(), status.Get_tag()

            if tag == TAG_HB:
                host, ts = data
                host_by_rank[src] = host
                last_hb[src] = ts
                # log opcional de HB:
                # log(f"HB <- rank {src} ({host})")

            elif tag == TAG_REQ:
                # Se há tarefa disponível: despacha
                if pending:
                    task_id = pending.popleft()
                    comm.send((CMD_WORK, task_id, task_ms), dest=src, tag=TAG_CMD)
                    in_flight[src] = (task_id, now())
                    log(f"dispatch -> rank {src} task={task_id}")
                else:
                    # Sem tarefa disponível AGORA:
                    # Não enviamos STOP ainda se ainda há tarefas em voo (poderão ser refeitas num timeout)
                    if done < n_tasks or in_flight:
                        # Deixa o worker bloqueado esperando o próximo comando
                        pass
                    else:
                        # Tudo concluído: já poderíamos enviar STOP (mas mandaremos depois em bloco)
                        pass

            elif tag == TAG_RES:
                task_id, elapsed, host = data
                done += 1
                in_flight.pop(src, None)
                last_hb[src] = now()
                log(f"result   <- rank {src} task={task_id} elapsed={elapsed:.3f}s")

        # 2) Verifica timeouts (falhas/lentidão) e refileira tarefas
        t = now()
        for r, (task_id, start_t) in list(in_flight.items()):
            if t - last_hb.get(r, 0.0) > timeout:
                # Considera o worker "suspeito/lento": reatribui task
                in_flight.pop(r, None)
                pending.appendleft(task_id)  # volta tarefa para a frente da fila
                log(f"TIMEOUT! rank {r} sem heartbeat dentro de {timeout:.2f}s; refileirando task={task_id}")

        time.sleep(0.001)  # evita busy-wait

        # 3) Se não há mais tarefas pendentes e nada em voo, encerramos o loop
        # (condição já controlada na guarda do while)

    t1 = now()

    # 4) STOP para todos os workers (garante término ordenado)
    for r in workers:
        try:
            comm.send((CMD_STOP, -1, 0), dest=r, tag=TAG_CMD)
        except Exception:
            pass

    # Relatório por host
    by_host = {}
    for r, h in host_by_rank.items():
        by_host.setdefault(h, []).append(r)

    log(f"fim: tasks={n_tasks} duracao={t1 - t0:.3f}s hosts={ {h: sorted(rs) for h, rs in by_host.items()} }")

# ---- WORKER ----
def worker(comm: MPI.Comm, jitter_fail: float = 0.0, hb_interval_ms: int = 100):
    """
    Worker com heartbeats:
      - envia heartbeat + request antes de pedir trabalho
      - durante execução envia heartbeats a cada hb_interval_ms
      - 'jitter_fail' pode simular atrasos (ex.: 2.5s por batimento) para testar tolerância
    """
    rank = comm.Get_rank()
    host = MPI.Get_processor_name()
    status = MPI.Status()

    log("WORKER iniciado")

    while True:
        # 1) heartbeat + pedido de trabalho
        log("REQUEST work + heartbeat")
        comm.send((host, now()), dest=0, tag=TAG_HB)
        comm.send(None,          dest=0, tag=TAG_REQ)

        # 2) recebe comando do mestre (bloqueante)
        cmd, task_id, task_ms = comm.recv(source=0, tag=TAG_CMD, status=status)
        log(f"cmd={cmd} task={task_id} ms={task_ms}")

        if cmd == CMD_STOP:
            log("STOP recebido, encerrando")
            break

        # 3) executa trabalho em pedaços, emitindo heartbeats periódicos
        t0 = now()
        ms_left = int(task_ms)
        while ms_left > 0:
            step = min(ms_left, hb_interval_ms)
            time.sleep(step / 1000.0)
            ms_left -= step
            comm.send((host, now()), dest=0, tag=TAG_HB)
            log("heartbeat (work em andamento)")
            if jitter_fail > 0.0:
                time.sleep(jitter_fail)  # simula travas/lentidão

        elapsed = now() - t0

        # 4) envia resultado ao mestre
        comm.send((task_id, elapsed, host), dest=0, tag=TAG_RES)
        log(f"RESULT -> task={task_id} elapsed={elapsed:.3f}s")

# ---- main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-tasks", type=int, default=40)
    ap.add_argument("--task-ms", type=int, default=250)
    ap.add_argument("--timeout", type=float, default=2.5)
    ap.add_argument("--fail-jitter", type=float, default=0.0,
                    help="atraso adicional (s) por batimento para simular lentidão/falha")
    args = ap.parse_args()

    if comm.Get_size() < 2:
        if RANK == 0:
            print("Precisa de >=2 processos.")
        MPI.COMM_WORLD.Abort(1)

    if RANK == 0:
        master(comm, args.n_tasks, args.task_ms, args.timeout)
    else:
        worker(comm, jitter_fail=args.fail_jitter)

if __name__ == "__main__":
    main()
