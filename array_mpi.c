#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int rank, size;
    long long N;
    int *arr = NULL;
    double start, end;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 2) {
        if (rank == 0)
            printf("Usage: mpirun -np <p> ./a.out <array_size>\n");
        MPI_Finalize();
        return 1;
    }

    N = atoll(argv[1]);

    arr = (int *)malloc(N * sizeof(int));

    for (long long i = 0; i < N; i++)
        arr[i] = i;

    long long local_n = N / size;
    long long start_index = rank * local_n;
    long long end_index;

    if (rank == size - 1)
        end_index = N;  
    else
        end_index = start_index + local_n;

    MPI_Barrier(MPI_COMM_WORLD);
    start = MPI_Wtime();

    long long local_sum = 0;

    for (long long i = start_index; i < end_index; i++)
        local_sum += arr[i];

    long long global_sum = 0;

    MPI_Reduce(&local_sum, &global_sum, 1,
               MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    end = MPI_Wtime();

    if (rank == 0) {
        printf("Array Size: %lld\n", N);
        printf("Processes: %d\n", size);
        printf("Total Run Time: %f seconds\n", end - start);
    }

    free(arr);
    MPI_Finalize();
    return 0;
}

