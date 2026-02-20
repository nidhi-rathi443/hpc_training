#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int rank, size;
    int N;
    int *data = NULL;
    int local_sum = 0, global_sum = 0;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0)
    {
        printf("Enter total number of elements:\n ");
        scanf("%d", &N);
        data = (int *)malloc(N * sizeof(int));
        printf("Enter %d numbers:\n", N);
        for (int i = 0; i < N; i++)
            scanf("%d", &data[i]);
    }

    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (rank != 0)
        data = (int *)malloc(N * sizeof(int));
    MPI_Bcast(data, N, MPI_INT, 0, MPI_COMM_WORLD);

    int base = N / size;        
    int remainder = N % size;   
    int start = rank * base;
    int end = start + base;
    if (rank == size - 1)
        end += remainder;
    for (int i = start; i < end; i++)
        local_sum += data[i];
    printf("Rank %d handles index %d to %d, Local Sum = %d\n",
           rank, start, end - 1, local_sum);
    MPI_Reduce(&local_sum, &global_sum, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
    {
        double avg = (double)global_sum / N;
        printf("Global Sum = %d\n", global_sum);
        printf("Average = %.2f\n", avg);
    }
    free(data);
    MPI_Finalize();
    return 0;
}

 