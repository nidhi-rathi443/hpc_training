#include<stdio.h>
#include<mpi.h>

int main(int argc, char *argv[]){
    int rank, size, i, local_sum=0;
    int arr[8]={1,2,3,4,5,6,7,8};
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Bcast(arr, 8, MPI_INT, 0, MPI_COMM_WORLD);
    for (int i = 0; i < 8; i++)
    {
        local_sum += arr[i];
    }
    printf("Process %d: Local Sum = %d\n", rank, local_sum);
    MPI_Finalize();
    return 0;
}