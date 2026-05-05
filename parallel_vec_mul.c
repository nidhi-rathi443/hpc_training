#include<stdio.h>
#include<mpi.h>

#define N 4
int main(int argc, char *argv[]){
    int rank, size;
    int A[N][N]={
            {1, 2, 3, 4},
            {5, 6, 7, 8},
            {9,10,11,12},
            {13,14,15,16}
        };      
    int x[N]={1,1,1,1};         
    int row[N];       
    int local_y;      
    int y[N]; 
    
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
        printf("Matrix A:\n");
        for (int i = 0; i < N; i++)
        {
            for (int j = 0; j < N; j++)
                printf("%3d ", A[i][j]);
            printf("\n");
        }

        printf("\nVector x:\n");
        for (int i = 0; i < N; i++)
            printf("%d ", x[i]);
        printf("\n\n");
    }

    MPI_Scatter(A, N, MPI_INT, row, N, MPI_INT, 0, MPI_COMM_WORLD);

    MPI_Bcast(x, N, MPI_INT, 0, MPI_COMM_WORLD);

    local_y = 0;
    for (int i = 0; i < N; i++)
        local_y += row[i] * x[i];

    printf("Rank %d computed y_%d = %d\n", rank, rank, local_y);

    MPI_Gather(&local_y, 1, MPI_INT, y, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank == 0)
    {
        printf("\nResult Vector y:\n");
        for (int i = 0; i < N; i++)
            printf("%d ", y[i]);
        printf("\n");
    }

    MPI_Finalize();
    return 0;

}