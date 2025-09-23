MPI em Python com mpi4py

Este repositório demonstra como programar MPI (Message Passing Interface) em Python usando mpi4py, cobrindo comunicação ponto-a-ponto, operações coletivas e um exemplo em pipeline. Os scripts medem tempo, speedup e eficiência.

Sumário

Pré-requisitos

Instalação

Windows (MS-MPI)

Linux (OpenMPI/MPICH)

macOS (Homebrew)

Verificação rápida

Estrutura do repositório

Como executar

Medições: tempo, speedup e eficiência

Erros comuns (e soluções)

Referências úteis

Licença

Pré-requisitos

Uma implementação de MPI instalada (OpenMPI, MPICH ou Microsoft MPI).

Python 3.8+.

Pacote mpi4py instalado no seu ambiente Python.

Dica: no Windows, use mpiexec; em Linux/macOS, mpiexec ou mpirun.

Instalação
Windows (MS-MPI)

Instale o Microsoft MPI (MS-MPI) (Redistributable e opcionalmente o SDK).
O binário costuma ficar em:
C:\Program Files\Microsoft MPI\Bin\mpiexec.exe
Adicione esse caminho à variável PATH.

Instale mpi4py:
pip install mpi4py


Linux (OpenMPI/MPICH)
# Debian/Ubuntu (OpenMPI)
sudo apt-get update
sudo apt-get install -y openmpi-bin libopenmpi-dev
pip install mpi4py

from mpi4py import MPI
comm = MPI.COMM_WORLD
print(f"Hello from rank {comm.Get_rank()} of {comm.Get_size()}")

mpiexec -n 4 python hello_mpi.py

Hello from rank 0 of 4
Hello from rank 1 of 4
Hello from rank 2 of 4
Hello from rank 3 of 4


Referências úteis

mpi4py — documentação oficial

MPI Standard — comunicadores, coletivas e ponto-a-ponto.

OpenMPI / MPICH / MS-MPI — instalações e uso do mpiexec/mpirun.

Licença

Este projeto está licenciado sob a MIT License. Sinta-se livre para usar e adaptar.
