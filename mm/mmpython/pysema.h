/* already defined in pythread.h */
/*typedef void *PyThread_type_sema;*/

PyThread_type_sema PyThread_allocate_sema(int);
void PyThread_free_sema(PyThread_type_sema);
int PyThread_down_sema(PyThread_type_sema, int);
#define WAIT_SEMA 1
#define NOWAIT_SEMA 0
void PyThread_up_sema(PyThread_type_sema);
