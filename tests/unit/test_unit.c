/*
** EPITECH PROJECT, 2025
** --
** File description:
** --
*/

#include <criterion/criterion.h>

#include "panoramix.h"

typedef struct {
    int pot_servings;
    int nb_refills_left;
    bool druid_done;
    bool refilling;
    int nb_waiting;
} snap_t;

static snap_t run_sim(int nv, int pot, int fights, int refills)
{
    state_t s = {0};
    pthread_t druid;
    pthread_t vthr[nv];
    villager_args_t vargs[nv];
    snap_t snap = {0};
    int i = 0;

    freopen("/dev/null", "w", stdout);
    init_state(&s, pot, refills);
    pthread_create(&druid, NULL, druid_thread, &s);
    for (i = 0; i < nv; i++) {
        vargs[i] = (villager_args_t){i, fights, &s};
        pthread_create(&vthr[i], NULL, villager_thread, &vargs[i]);
    }
    for (i = 0; i < nv; i++)
        pthread_join(vthr[i], NULL);
    s.all_done = true;
    sem_post(&s.druid_wake);
    pthread_join(druid, NULL);
    snap = (snap_t){s.pot_servings, s.nb_refills_left,
        s.druid_done, s.refilling, s.nb_waiting};
    cleanup_state(&s);
    return snap;
}

Test(state_init, returns_true)
{
    state_t s = {0};
    cr_assert(init_state(&s, 5, 3));
    cleanup_state(&s);
}

Test(state_init, pot_servings_equals_pot_size)
{
    state_t s = {0};
    init_state(&s, 7, 2);
    cr_assert_eq(s.pot_servings, 7);
    cleanup_state(&s);
}

Test(state_init, pot_size_stored)
{
    state_t s = {0};
    init_state(&s, 12, 1);
    cr_assert_eq(s.pot_size, 12);
    cleanup_state(&s);
}

Test(state_init, nb_refills_stored)
{
    state_t s = {0};
    init_state(&s, 5, 9);
    cr_assert_eq(s.nb_refills_left, 9);
    cleanup_state(&s);
}

Test(state_init, nb_waiting_zero)
{
    state_t s = {0};
    init_state(&s, 5, 3);
    cr_assert_eq(s.nb_waiting, 0);
    cleanup_state(&s);
}

Test(state_init, druid_done_false)
{
    state_t s = {0};
    init_state(&s, 5, 3);
    cr_assert(!s.druid_done);
    cleanup_state(&s);
}

Test(state_init, all_done_false)
{
    state_t s = {0};
    init_state(&s, 5, 3);
    cr_assert(!s.all_done);
    cleanup_state(&s);
}

Test(state_init, refilling_false)
{
    state_t s = {0};
    init_state(&s, 5, 3);
    cr_assert(!s.refilling);
    cleanup_state(&s);
}

Test(state_init, mutex_is_usable)
{
    state_t s = {0};
    init_state(&s, 5, 3);
    cr_assert_eq(pthread_mutex_trylock(&s.mutex), 0);
    pthread_mutex_unlock(&s.mutex);
    cleanup_state(&s);
}

Test(state_init, min_values)
{
    state_t s = {0};
    cr_assert(init_state(&s, 1, 1));
    cr_assert_eq(s.pot_servings, 1);
    cr_assert_eq(s.nb_refills_left, 1);
    cleanup_state(&s);
}

Test(state_init, large_values)
{
    state_t s = {0};
    cr_assert(init_state(&s, 1000, 500));
    cr_assert_eq(s.pot_servings, 1000);
    cr_assert_eq(s.nb_refills_left, 500);
    cleanup_state(&s);
}

Test(state_init, cleanup_no_crash)
{
    state_t s = {0};
    init_state(&s, 5, 3);
    cleanup_state(&s);
    cr_assert(true);
}

Test(sim, one_fight_depletes_pot_by_one)
{
    snap_t r = run_sim(1, 5, 1, 1);
    cr_assert_eq(r.pot_servings, 4);
}

Test(sim, three_fights_depletes_pot_by_three)
{
    snap_t r = run_sim(1, 10, 3, 1);
    cr_assert_eq(r.pot_servings, 7);
}

Test(sim, five_fights_depletes_pot_by_five)
{
    snap_t r = run_sim(1, 10, 5, 1);
    cr_assert_eq(r.pot_servings, 5);
}

Test(sim, pot_never_negative)
{
    snap_t r = run_sim(1, 3, 3, 1);
    cr_assert_geq(r.pot_servings, 0);
}

Test(sim, pot_never_exceeds_pot_size)
{
    snap_t r = run_sim(1, 5, 3, 2);
    cr_assert_leq(r.pot_servings, 5);
}

Test(sim, no_refill_when_enough_pot)
{
    snap_t r = run_sim(1, 10, 3, 5);
    cr_assert_eq(r.nb_refills_left, 5);
}

Test(sim, druid_not_done_when_no_refill_needed)
{
    snap_t r = run_sim(1, 10, 3, 5);
    cr_assert(!r.druid_done);
}

Test(sim, refill_triggered_when_pot_depleted)
{
    snap_t r = run_sim(1, 2, 3, 5);
    cr_assert_lt(r.nb_refills_left, 5);
}

Test(sim, druid_done_after_last_refill)
{
    snap_t r = run_sim(1, 1, 3, 2);
    cr_assert(r.druid_done);
    cr_assert_eq(r.nb_refills_left, 0);
}

Test(sim, refilling_flag_reset_after_sim)
{
    snap_t r = run_sim(1, 1, 3, 3);
    cr_assert(!r.refilling);
}

Test(sim, nb_waiting_zero_after_sim)
{
    snap_t r = run_sim(3, 2, 2, 3);
    cr_assert_eq(r.nb_waiting, 0);
}

Test(sim, two_villagers_deplete_twice)
{
    snap_t r = run_sim(2, 10, 1, 1);
    cr_assert_eq(r.pot_servings, 8);
}

Test(sim, exact_pot_size_fights_no_refill)
{
    snap_t r = run_sim(1, 5, 5, 3);
    cr_assert_eq(r.pot_servings, 0);
    cr_assert_eq(r.nb_refills_left, 3);
}

Test(sim, pot_size_one_each_fight_triggers_refill)
{
    snap_t r = run_sim(1, 1, 3, 2);
    cr_assert_eq(r.nb_refills_left, 0);
    cr_assert(r.druid_done);
}

Test(sim, large_pot_one_fight)
{
    snap_t r = run_sim(1, 100, 1, 1);
    cr_assert_eq(r.pot_servings, 99);
    cr_assert(!r.druid_done);
}

Test(sim, multiple_villagers_share_pot)
{
    snap_t r = run_sim(5, 20, 1, 1);
    cr_assert_eq(r.pot_servings, 15);
    cr_assert(!r.druid_done);
}

Test(sim, many_refills_all_used)
{
    snap_t r = run_sim(1, 1, 5, 4);
    cr_assert_eq(r.nb_refills_left, 0);
    cr_assert(r.druid_done);
}

Test(sim, refills_count_decrements_correctly)
{
    snap_t r = run_sim(1, 2, 4, 5);
    cr_assert_lt(r.nb_refills_left, 5);
}

Test(sim, concurrent_access_no_negative_pot)
{
    snap_t r = run_sim(10, 5, 2, 5);
    cr_assert_geq(r.pot_servings, 0);
}

Test(sim, concurrent_access_pot_stays_valid)
{
    snap_t r = run_sim(10, 5, 2, 5);
    cr_assert_leq(r.pot_servings, 5);
}

Test(sim, druid_done_consistent_with_refills)
{
    snap_t r = run_sim(2, 3, 5, 4);
    cr_assert_eq(r.druid_done, r.nb_refills_left == 0);
}

Test(sim, single_villager_many_fights_enough_refills)
{
    snap_t r = run_sim(1, 1, 10, 9);
    cr_assert_eq(r.nb_refills_left, 0);
    cr_assert(r.druid_done);
}
