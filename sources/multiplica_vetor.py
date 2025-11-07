import time

# python3 multiplica_vetor.py
# C[0][0] = 1000
# Tempo de multiplicacao: 144.222 s

def matmul_ikj(A, B):
    n = len(A)
    # cria C cheia de zeros
    C = [[0] * n for _ in range(n)]

    # ordem i-k-j para melhor reaproveitamento de A[i][k]
    for i in range(n):
        for k in range(n):
            aik = A[i][k]
            # percorre linha de B[k] inteira
            for j in range(n):
                C[i][j] += aik * B[k][j]
    return C


def main():
    N = 1000  # cuidado: 1000 em Python puro vai demorar bem mais que em C++
              # aumente aos poucos: 200, 300, 500...

    # monta A e B cheias de 1, igual ao C++
    A = [[1] * N for _ in range(N)]
    B = [[1] * N for _ in range(N)]

    t0 = time.perf_counter()
    C = matmul_ikj(A, B)
    t1 = time.perf_counter()

    print("C[0][0] =", C[0][0])  # deve dar N (soma de N produtos 1*1)
    print(f"Tempo de multiplicacao: {t1 - t0:0.3f} s")


if __name__ == "__main__":
    main()
