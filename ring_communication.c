#include<stdio.h>
#include<mpi.h>

int main(int argc, char *argv[]){
    int rank, size, send, recieve;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size); 

    send = rank;

    int next = (rank+1) % size;
    int prev = (rank-1+size) % size;

    MPI_Send(&send, 1, MPI_INT, next, 0, MPI_COMM_WORLD);
    MPI_Recv(&recieve, 1, MPI_INT, prev, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    
    printf("Rank %d received %d\n", rank, recieve);

    MPI_Finalize();
    return 0;
}

