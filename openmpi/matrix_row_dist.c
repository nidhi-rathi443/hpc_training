#include<stdio.h>
#include<stdlib.h>
#include<mpi.h>

#define N 4
int main(int argc, char *argv[]){
    int rank, size;
    int matrix[N][N];
    int row[N];
    int local_sum=0;
    int global_sum=0;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if(size!=N){
        if(rank==0){
            printf("Run with %d processes:\n", N);
        }
        MPI_Finalize();
        return 0;
    }

    if(rank==0){
        int temp[N][N] = {
            {1,  2,  3,  4},
            {5,  6,  7,  8},
            {9, 10, 11, 12},
            {13, 14, 15, 16}
        };

        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                matrix[i][j] = temp[i][j];

        printf("Matrix:\n");
        for (int i = 0; i < N; i++)
        {
            for (int j = 0; j < N; j++)
                printf("%3d ", matrix[i][j]);
            printf("\n");
        }
        printf("\n");
    }

    MPI_Scatter(matrix, N, MPI_INT, row, N, MPI_INT, 0, MPI_COMM_WORLD);

    for (int i = 0; i < N; i++)
        local_sum += row[i];
    printf("Rank %d received row, Local Row Sum = %d\n", rank, local_sum);

     MPI_Reduce(&local_sum, &global_sum, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0)
    {
        printf("\nTotal Matrix Sum = %d\n", global_sum);
    }

    MPI_Finalize();
    return 0;
}