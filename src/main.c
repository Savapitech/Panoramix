/*
** EPITECH PROJECT, 2025
** --
** File description:
** --
*/

#include "panoramix.h"

static
bool parse_args(int argc, char **argv, int params[4])
{
    int i = 0;

    if (argc != 5) {
        printf("USAGE: %s <nb_villagers> <pot_size>"
            " <nb_fights> <nb_refills>\n", argv[0]);
        return false;
    }
    for (i = 0; i < 4; i++) {
        params[i] = atoi(argv[i + 1]);

        if (params[i] <= 0) {
            printf("USAGE: %s <nb_villagers> <pot_size>"
                " <nb_fights> <nb_refills>\n", argv[0]);
            printf("Values must be >0.\n");
            return false;
        }
    }
    return true;
}

static
bool run_simulation(int params[4])
{
    state_t state = {0};
    pthread_t druid;
    pthread_t villagers[params[0]];
    villager_args_t vargs[params[0]];
    int i = 0;

    if (!init_state(&state, params[1], params[3]))
        return false;
    pthread_create(&druid, NULL, druid_thread, &state);
    for (i = 0; i < params[0] && i < MAX_VILLAGERS; i++) {
        vargs[i] = (villager_args_t){i, params[2], &state};
        pthread_create(&villagers[i], NULL, villager_thread, &vargs[i]);
    }
    for (i = 0; i < params[0] && i < MAX_VILLAGERS; i++)
        pthread_join(villagers[i], NULL);
    state.all_done = true;
    sem_post(&state.druid_wake);
    pthread_join(druid, NULL);
    cleanup_state(&state);
    return true;
}

int main(int argc, char **argv)
{
    int params[4] = {0};

    if (!parse_args(argc, argv, params))
        return RETURN_FAIL;
    return run_simulation(params) ? RETURN_SUCCESS : RETURN_FAIL;
}
