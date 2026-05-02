/*
** EPITECH PROJECT, 2025
** --
** File description:
** --
*/

#include "panoramix.h"

static
bool do_refill(state_t *state)
{
    int to_wake = 0;
    bool done = false;

    pthread_mutex_lock(&state->mutex);
    state->nb_refills_left--;
    printf("Druid: Ah! Yes, yes, I'm awake! Working on it!"
        " Beware I can only make %d more refills"
        " after this one.\n", state->nb_refills_left);
    state->pot_servings = state->pot_size;
    state->refilling = false;
    to_wake = state->nb_waiting;
    state->nb_waiting = 0;
    done = (!state->nb_refills_left);
    state->druid_done = done;
    if (done)
        printf("Druid: I'm out of viscum. I'm going back to... zZz\n");
    pthread_mutex_unlock(&state->mutex);
    for (int i = 0; i < to_wake; i++)
        sem_post(&state->pot_refilled);
    return done;
}

void *druid_thread(void *arg)
{
    state_t *state = (state_t *)arg;
    bool stop = false;

    printf("Druid: I'm ready... but sleepy...\n");
    while (!stop) {
        sem_wait(&state->druid_wake);
        if (state->all_done)
            break;
        stop = do_refill(state);
    }
    return NULL;
}
