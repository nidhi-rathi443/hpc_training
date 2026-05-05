#include<stdio.h>
#include<mpi.h>
#include<stdlib.h>

int main(int argc, char *argv[]){
    int rank, i, size, N=8, c[N];
    int local_n;
    int *local_A, *local_B, *local_C;
    int a[]={1,2,3,4,5,6,7,8};
    int b[]={8,7,6,5,4,3,2,1};
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    local_n = N / size;
    local_A = (int *)malloc(local_n * sizeof(int));
    local_B = (int *)malloc(local_n * sizeof(int));
    local_C = (int *)malloc(local_n * sizeof(int));
    if(rank==0){
        printf("Vector A: ");
        for (int i = 0; i < N; i++)
            printf("%d ", a[i]);
        printf("\n");

        printf("Vector B: ");
        for (int i = 0; i < N; i++)
            printf("%d ", b[i]);
        printf("\n");
    }
    MPI_Scatter(a, local_n, MPI_INT, local_A, local_n, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Scatter(b, local_n, MPI_INT, local_B, local_n, MPI_INT, 0, MPI_COMM_WORLD);
    for (int i = 0; i < local_n; i++)
    {
        local_C[i] = local_A[i] + local_B[i];
    }
    MPI_Gather(local_C, local_n, MPI_INT, c , local_n, MPI_INT, 0, MPI_COMM_WORLD);
    if (rank == 0)
    {
        printf("Result Vector C (A+B): ");
        for (int i = 0; i < N; i++)
            printf("%d ", c[i]);
        printf("\n");
    }

    free(local_A);
    free(local_B);
    free(local_C);
    MPI_Finalize();
    return 0;
}
