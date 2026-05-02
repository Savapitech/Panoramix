/*
** EPITECH PROJECT, 2025
** Panoramix
** File description:
** state.c
*/

#include "panoramix.h"

bool init_state(state_t *state, int pot_size, int nb_refills)
{
    state->pot_servings = pot_size;
    state->pot_size = pot_size;
    state->nb_refills_left = nb_refills;
    state->nb_waiting = 0;
    state->druid_done = false;
    state->all_done = false;
    state->refilling = false;
    if (pthread_mutex_init(&state->mutex, NULL) != 0)
        return false;
    if (sem_init(&state->druid_wake, 0, 0) != 0)
        return false;
    if (sem_init(&state->pot_refilled, 0, 0) != 0)
        return false;
    return true;
}

void cleanup_state(state_t *state)
{
    pthread_mutex_destroy(&state->mutex);
    sem_destroy(&state->druid_wake);
    sem_destroy(&state->pot_refilled);
}
