/*
** EPITECH PROJECT, 2025
** ---
** File description:
** ---
*/

#ifndef PANORAMIX
    #define PANORAMIX

    #include <pthread.h>
    #include <semaphore.h>
    #include <stdbool.h>
    #include <stdatomic.h>
    #include <stdio.h>
    #include <stdlib.h>

    #define RETURN_SUCCESS 0
    #define RETURN_FAIL 84
    #define MAX_VILLAGERS 50000

typedef struct {
    int pot_servings;
    int pot_size;
    int nb_refills_left;
    int nb_waiting;
    bool druid_done;
    _Atomic bool all_done;
    bool refilling;
    pthread_mutex_t mutex;
    sem_t druid_wake;
    sem_t pot_refilled;
} state_t;

typedef struct {
    int id;
    int nb_fights;
    state_t *state;
} villager_args_t;

bool init_state(state_t *state, int pot_size, int nb_refills);
void cleanup_state(state_t *state);
void *villager_thread(void *arg);
void *druid_thread(void *arg);

#endif
