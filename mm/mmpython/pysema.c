/*
 * Semaphore support.
 */

typedef void *PyThread_type_sema;
#include "pysema.h"
#include <pthread.h>

/* try to determine what version of the Pthread Standard is installed.
 * this is important, since all sorts of parameter types changed from
 * draft to draft and there are several (incompatible) drafts in
 * common use.  these macros are a start, at least. 
 * 12 May 1997 -- david arnold <davida@pobox.com>
*/

#if defined(__ultrix) && defined(__mips) && defined(_DECTHREADS_)
/* _DECTHREADS_ is defined in cma.h which is included by pthread.h */
#  define PY_PTHREAD_D4

#elif defined(__osf__) && defined (__alpha)
/* _DECTHREADS_ is defined in cma.h which is included by pthread.h */
#  if !defined(_PTHREAD_ENV_ALPHA) || defined(_PTHREAD_USE_D4) || defined(PTHREAD_USE_D4)
#    define PY_PTHREAD_D4
#  else
#    define PY_PTHREAD_STD
#  endif

#elif defined(_AIX)
/* SCHED_BG_NP is defined if using AIX DCE pthreads
 * but it is unsupported by AIX 4 pthreads. Default
 * attributes for AIX 4 pthreads equal to NULL. For
 * AIX DCE pthreads they should be left unchanged.
 */
#  if !defined(SCHED_BG_NP)
#    define PY_PTHREAD_STD
#  else
#    define PY_PTHREAD_D7
#  endif

#elif defined(__DGUX)
#  define PY_PTHREAD_D6

#elif defined(__hpux) && defined(_DECTHREADS_)
#  define PY_PTHREAD_D4

#else /* Default case */
#  define PY_PTHREAD_STD

#endif

#if defined(PY_PTHREAD_D4) || defined(PY_PTHREAD_D7)
#  define pthread_mutexattr_default pthread_mutexattr_default
#  define pthread_condattr_default pthread_condattr_default
#elif defined(PY_PTHREAD_STD) || defined(PY_PTHREAD_D6)
#  define pthread_mutexattr_default ((pthread_mutexattr_t *)NULL)
#  define pthread_condattr_default ((pthread_condattr_t *)NULL)
#endif

#define CHECK_STATUS(name)  if (status != 0) { perror(name); error = 1; }

struct semaphore {
	pthread_mutex_t mutex;
	pthread_cond_t cond;
	int value;
};

PyThread_type_sema 
PyThread_allocate_sema(int value)
{
	struct semaphore *sema;
	int status, error = 0;

	PyThread_init_thread();

	sema = (struct semaphore *) malloc(sizeof(struct semaphore));
	if (sema != NULL) {
		sema->value = value;
		status = pthread_mutex_init(&sema->mutex,
					    pthread_mutexattr_default);
		CHECK_STATUS("pthread_mutex_init");
		status = pthread_cond_init(&sema->cond,
					   pthread_condattr_default);
		CHECK_STATUS("pthread_cond_init");
		if (error) {
			free((void *) sema);
			sema = NULL;
		}
	}
	return (PyThread_type_sema) sema;
}

void PyThread_free_sema(PyThread_type_sema sema)
{
	int status, error = 0;
	struct semaphore *thesema = (struct semaphore *) sema;

	status = pthread_cond_destroy(&thesema->cond);
	CHECK_STATUS("pthread_cond_destroy");
	status = pthread_mutex_destroy(&thesema->mutex);
	CHECK_STATUS("pthread_mutex_destroy");
	free((void *) thesema);
}

int PyThread_down_sema(PyThread_type_sema sema, int waitflag)
{
	int status, error = 0, success;
	struct semaphore *thesema = (struct semaphore *) sema;

	status = pthread_mutex_lock(&thesema->mutex);
	CHECK_STATUS("pthread_mutex_lock");
	if (waitflag) {
		while (!error && thesema->value <= 0) {
			status = pthread_cond_wait(&thesema->cond,
						   &thesema->mutex);
			CHECK_STATUS("pthread_cond_wait");
		}
	}
	if (error)
		success = 0;
	else if (thesema->value > 0) {
		thesema->value--;
		success = 1;
	}
	else
success = 0;
	status = pthread_mutex_unlock(&thesema->mutex);
	CHECK_STATUS("pthread_mutex_unlock");
	return success;
}

void PyThread_up_sema(PyThread_type_sema sema)
{
	int status, error = 0;
	struct semaphore *thesema = (struct semaphore *) sema;

	status = pthread_mutex_lock(&thesema->mutex);
	CHECK_STATUS("pthread_mutex_lock");
	thesema->value++;
	status = pthread_cond_signal(&thesema->cond);
	CHECK_STATUS("pthread_cond_signal");
	status = pthread_mutex_unlock(&thesema->mutex);
	CHECK_STATUS("pthread_mutex_unlock");
}
