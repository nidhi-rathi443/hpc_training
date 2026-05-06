#include<stdio.h>
#include<mpi.h>
#define N 4

int main(int argc, char *argv[]){
    int rank, size;
    int A[N][N]={
        {2,3,1,4},
        {6,8,5,7},
        {9,12,10,11},
        {16,17,14,15}
    };
    int row[N];
    int local_max, global_max;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    if (size != N)
    {
        if (rank == 0)
            printf("Run with %d processes!\n", N);
        MPI_Finalize();
        return 0;
    }
    if (rank == 0)
    {
        printf("Matrix:\n");
        for (int i = 0; i < N; i++)
        {
            for (int j = 0; j < N; j++)
                printf("%3d ", A[i][j]);
            printf("\n");
        }
        printf("\n");
    }
    MPI_Scatter(A, N, MPI_INT, row, N, MPI_INT, 0, MPI_COMM_WORLD);
    local_max = row[0];
    for (int i = 1; i < N; i++)
    {
        if (row[i] > local_max)
            local_max = row[i];
    }
    printf("Rank %d local max = %d\n", rank, local_max);
    MPI_Reduce(&local_max, &global_max, 1,
               MPI_INT, MPI_MAX,
               0, MPI_COMM_WORLD);
    if (rank == 0)
    {
        printf("\nGlobal Maximum = %d\n", global_max);
    }
    MPI_Finalize();
    return 0;
}