#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#include "../plc_state_manager.h"
#include "log.h"
#include "utils.h"
#include "watchdog.h"

atomic_long plc_heartbeat;
extern PLCState plc_state;

void *watchdog_thread(void *arg)
{
    (void)arg;
    long last = atomic_load(&plc_heartbeat);

    while (1)
    {
        sleep(2); // Watch every 2 seconds

        if (plc_get_state() != PLC_STATE_RUNNING)
        {
            continue; // Only monitor when PLC is running
        }

        long now = atomic_load(&plc_heartbeat);
        if (now == last)
        {
            log_error("Watchdog: No heartbeat detected - PLC program is unresponsive");
            log_error("The loaded PLC program may contain an infinite loop. "
                      "Upload a corrected program to recover.");

            // Transition to ERROR state instead of killing the process.
            // This keeps the runtime alive so the webserver can still
            // communicate with it and upload a new program.
            // Writing directly to plc_state is safe here because the PLC
            // thread is unresponsive (stuck) and not contending the variable.
            // The main loop checks plc_state each cycle and will exit.
            plc_state = PLC_STATE_ERROR;
            log_info("PLC State: ERROR");

            // Reset heartbeat tracking for next run
            last = 0;
            atomic_store(&plc_heartbeat, 0);
            continue;
        }

        last = now;
    }

    return NULL;
}

int watchdog_init(void)
{
    pthread_t wd_thread;
    if (pthread_create(&wd_thread, NULL, watchdog_thread, NULL) != 0)
    {
        log_error("Failed to create watchdog thread");
        return -1;
    }
    pthread_detach(wd_thread); // Detach the thread to avoid memory leaks
    return 0;
}
