# mpi_checkpoint_demo.py
# ------------------------------------------------------------
# Checkpoint/Restart acadêmico com mpi4py
# - Cada rank salva periodicamente seu estado em disco (NPZ)
# - Rank 0 mantém um "manifesto" JSON com o último step confirmado
# - Em caso de queda, relance o job e ele retoma do checkpoint
#
# Execução (exemplos):
#   mpiexec -n 4 python3 mpi_checkpoint_demo.py --n 20000000 --iters 20 --ckpt-every 5
#   # simule uma falha:
#   mpiexec -n 4 python3 mpi_checkpoint_demo.py --n 20000000 --iters 20 --ckpt-every 5 --fail-rank 2 --fail-at 7
#   # depois relance SEM as flags de falha para retomar:
#   mpiexec -n 4 python3 mpi_checkpoint_demo.py --n 20000000 --iters 20 --ckpt-every 5
#
# O "problema" resolvido:
#   Soma de um vetor grande v[i] = i (distribuído por blocos) repetida ao longo
#   de 'iters' "passos" (pense como um loop de tempo). Em cada passo calculamos
#   uma pequena função do bloco e acumulamos uma métrica global (allreduce).
#   O checkpoint salva: step, acumuladores locais e posição do bloco.
# ------------------------------------------------------------
from mpi4py import MPI
import numpy as np
import json, os, shutil, argparse, time

COMM = MPI.COMM_WORLD
RANK = COMM.Get_rank()
SIZE = COMM.Get_size()
HOST = MPI.Get_processor_name()

def log(msg: str):
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    ms = int((time.time() % 1)*1000)
    print(f"[{t}.{ms:03d}] [rank {RANK}] [host {HOST}] {msg}", flush=True)

def atomic_write(path_tmp: str, path_final: str, bytes_writer):
    """Escreve em arquivo temporário e faz rename atômico."""
    with open(path_tmp, "wb") as f:
        bytes_writer(f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(path_tmp, path_final)

def save_manifest(manifest_path: str, data: dict):
    tmp = manifest_path + ".tmp"
    def _w(f):
        f.write(json.dumps(data, indent=2).encode("utf-8"))
    atomic_write(tmp, manifest_path, _w)

def load_manifest(manifest_path: str):
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_rank_ckpt(ckpt_dir: str, step: int, acc_local: float, lo: int, hi: int):
    path = os.path.join(ckpt_dir, f"rank{RANK}.npz")
    tmp = path + ".tmp"
    def _w(fobj):
        np.savez(fobj, step=np.int64(step), acc=float(acc_local), lo=np.int64(lo), hi=np.int64(hi))
    atomic_write(tmp, path, _w)

def load_rank_ckpt(ckpt_dir: str):
    path = os.path.join(ckpt_dir, f"rank{RANK}.npz")
    if not os.path.exists(path):
        return None
    try:
        with np.load(path) as z:
            return {
                "step": int(z["step"]),
                "acc": float(z["acc"]),
                "lo": int(z["lo"]),
                "hi": int(z["hi"]),
            }
    except Exception:
        return None

def split_range(n: int, p: int, r: int):
    """Divide 0..n-1 em p blocos; retorna [lo, hi) do rank r."""
    base = n // p
    rem  = n % p
    lo   = r*base + min(r, rem)
    hi   = lo + base + (1 if r < rem else 0)
    return lo, hi

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000_000, help="tamanho do vetor global")
    ap.add_argument("--iters", type=int, default=20, help="número de passos (tempo) a executar")
    ap.add_argument("--ckpt-every", type=int, default=5, help="periodicidade do checkpoint (em passos)")
    ap.add_argument("--ckpt-dir", type=str, default="./ckpt_demo", help="pasta de checkpoints")
    ap.add_argument("--fail-rank", type=int, default=-1, help="rank que irá 'falhar' (simulação)")
    ap.add_argument("--fail-at", type=int, default=-1, help="passo no qual o rank falha (simulação)")
    args = ap.parse_args()

    # Partição do vetor global por blocos
    lo, hi = split_range(args.n, SIZE, RANK)
    nloc   = hi - lo

    # Aloca bloco local determinístico: v[i] = i (no domínio global)
    # Para não ocupar RAM demais em n muito grande, computamos sob demanda.
    # Aqui, opcionalmente, criamos um "view" virtual (usaremos fórmulas).
    def local_sum_formula():
        # soma de lo..(hi-1) = (hi-1 + lo)*nloc/2
        return 0.5*( (hi-1) + lo )*nloc

    # Carrega checkpoints se existirem
    os.makedirs(args.ckpt_dir, exist_ok=True)
    manifest_path = os.path.join(args.ckpt_dir, "manifest.json")

    # Cada rank lê o seu checkpoint local
    my_ckpt = load_rank_ckpt(args.ckpt_dir)
    # Rank 0 lê o manifesto global (último step fechado)
    if RANK == 0:
        manifest = load_manifest(manifest_path) or {"last_complete_step": -1, "size": SIZE}
        # Se o tamanho do comunicador mudou, reiniciamos do zero por segurança
        if manifest.get("size", SIZE) != SIZE:
            log("Aviso: SIZE mudou desde o último run; reiniciando do passo -1.")
            manifest = {"last_complete_step": -1, "size": SIZE}
    else:
        manifest = None
    manifest = COMM.bcast(manifest, root=0)

    # O step inicial é: mínimo entre meu checkpoint e manifesto (consistente global)
    my_start = my_ckpt["step"] if my_ckpt is not None else -1
    start_step = min(my_start, manifest["last_complete_step"])
    if start_step < 0:
        acc_local = 0.0
    else:
        acc_local = my_ckpt["acc"] if my_ckpt is not None else 0.0

    if RANK == 0:
        log(f"Retomando do passo {start_step} (manifesto={manifest['last_complete_step']}). "
            f"Blocagem: n={args.n} | SIZE={SIZE} | local=[{lo},{hi}) nloc={nloc}")

    # Loop principal de "tempo"
    for step in range(start_step + 1, args.iters):
        # --- Simulação de falha didática ---
        if RANK == args.fail_rank and step == args.fail_at:
            log(f"Simulando FALHA no passo {step} — finalizando o processo!")
            # Flush e abort somente do rank para simular crash.
            # Em muitos MPIs, uma queda encerra o job inteiro; para testar restart,
            # rode este passo e depois relance o job.
            os._exit(1)

        # “Trabalho”: soma determinística do bloco (poderia ser SpMV, stencil, etc.)
        # Aqui fazemos uma métrica que depende do passo para mostrar progressão.
        # Por ex., accumulate += sum(v) / (step+1)
        partial = local_sum_formula() / float(step + 1)
        acc_local += partial

        # Métrica global (ex.: norma, custo, etc.)
        acc_global = COMM.allreduce(acc_local, op=MPI.SUM)
        if RANK == 0 and (step % 1 == 0):
            log(f"step={step}  acc_global={acc_global:,.3f}")

        # Checkpoint periódico:
        if (step % args.ckpt_every) == 0 or (step == args.iters - 1):
            # 1) cada rank escreve seu NPZ
            save_rank_ckpt(args.ckpt_dir, step, acc_local, lo, hi)
            COMM.Barrier()  # coordena “commit”
            # 2) rank 0 atualiza manifesto indicando “last_complete_step=step”
            if RANK == 0:
                save_manifest(manifest_path, {"last_complete_step": step, "size": SIZE})
                log(f"[checkpoint] passo {step} salvo.")

    if RANK == 0:
        log("Finalizado com sucesso.")

if __name__ == "__main__":
    main()
