#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int rank, size;
    int value;
    int manual_total = 0;
    int reduce_total = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    value = rank * rank;

    if (rank == 0)
    {
        manual_total = value;

        for (int i = 1; i < size; i++)
        {
            int recv_value;
            MPI_Recv(&recv_value, 1, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            manual_total += recv_value;
        }
    }
    else
    {
        MPI_Send(&value, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
    }

    MPI_Reduce(&value, &reduce_total, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0)
    {
        printf("Reduce Total  = %d\n", reduce_total);
    }

    MPI_Finalize();
    return 0;
}