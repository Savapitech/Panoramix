/*
** EPITECH PROJECT, 2025
** --
** File description:
** --
*/

#include "panoramix.h"

static
void call_druid(state_t *state, int id)
{
    if (!state->refilling) {
        state->refilling = true;
        printf("Villager %d: Hey Pano wake up!"
            " We need more potion.\n", id);
        sem_post(&state->druid_wake);
    }
    state->nb_waiting++;
    pthread_mutex_unlock(&state->mutex);
    sem_wait(&state->pot_refilled);
    pthread_mutex_lock(&state->mutex);
}

static
bool take_potion(state_t *state, int id)
{
    pthread_mutex_lock(&state->mutex);
    printf("Villager %d: I need a drink..."
        " I see %d servings left.\n",
        id, state->pot_servings);
    while (state->pot_servings == 0) {
        if (state->druid_done) {
            pthread_mutex_unlock(&state->mutex);
            return false;
        }
        call_druid(state, id);
    }
    state->pot_servings--;
    pthread_mutex_unlock(&state->mutex);
    return true;
}

void *villager_thread(void *arg)
{
    villager_args_t *vargs = (villager_args_t *)arg;
    int id = vargs->id;
    int nb_fights = vargs->nb_fights;
    state_t *state = vargs->state;
    int fights_left = nb_fights;

    printf("Villager %d: Going into battle!\n", id);
    while (fights_left > 0) {
        if (!take_potion(state, id))
            break;
        fights_left--;
        printf("Villager %d: Take that roman scum!"
            " Only %d left.\n", id, fights_left);
    }
    printf("Villager %d: I'm going to sleep now.\n", id);
    return NULL;
}
