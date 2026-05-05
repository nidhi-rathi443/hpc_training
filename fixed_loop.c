#include <stdio.h>
#include <mpi.h>

int main(int argc, char **argv)
{
    int i, rank, nprocs;
    int count, start, stop;
    int nloops, total_nloops;
    int total_iterations = 1000;

    MPI_Init(&argc, &argv);

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);

    // Workers divide work among themselves (exclude p0)
    count = 1000 / (nprocs - 1);   // 1000/3 = 333

    nloops = 0;

    if (rank != 0)
    {
        // WORKER PROCESSES (p1, p2, p3)

        start = (rank - 1) * count;
        stop  = start + count;

        for (i = start; i < stop; ++i)
        {
            ++nloops;
        }

        printf("Process %d performed %d iterations of the loop.\n",
               rank, nloops);

        // Send to master
        MPI_Send(&nloops, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
    }
    else
    {
        // MASTER PROCESS (p0)

        total_nloops = 0;

        // Receive from workers
        for (i = 1; i < nprocs; ++i)
        {
            MPI_Recv(&nloops, 1, MPI_INT, i, 0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);

            total_nloops += nloops;
        }

        // Perform remaining iterations
        int remaining = total_iterations - total_nloops;

        nloops = 0;
        for (i = 0; i < remaining; ++i)
        {
            ++nloops;
        }

        printf("Process 0 performed %d remaining iterations of the loop.\n",
               nloops);

    }

    MPI_Finalize();
    return 0;
}

