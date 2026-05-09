#!/usr/bin/env python3

import sys
import re
import os
import subprocess
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button

BG     = '#0d1117'
PANEL  = '#161b22'
BORDER = '#30363d'
TEXT   = '#c9d1d9'
MUTED  = '#8b949e'
ACCENT = '#58a6ff'
DARK   = '#21262d'

STATE_COLORS = {
    'ready':    '#388bfd',
    'battle':   '#e3b341',
    'waiting':  '#f85149',
    'fighting': '#3fb950',
    'sleeping': '#30363d',
}

DRUID_COLORS = {
    'sleeping':  '#e3b341',
    'refilling': '#3fb950',
    'done':      '#f85149',
}


def parse_args():
    if len(sys.argv) != 5:
        print(f"USAGE: {sys.argv[0]} <nb_villagers> <pot_size> <nb_fights> <nb_refills>")
        sys.exit(84)
    try:
        params = [int(x) for x in sys.argv[1:]]
    except ValueError:
        sys.exit(84)
    if any(p <= 0 for p in params):
        print("Values must be >0.")
        sys.exit(84)
    return params


def run_simulation(params):
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    binary = os.path.join(root, 'panoramix')
    if not os.path.isfile(binary):
        print(f"panoramix binary not found at {binary}")
        sys.exit(84)
    proc = subprocess.run(
        [binary] + [str(p) for p in params],
        capture_output=True, text=True, cwd=root
    )
    return [l for l in proc.stdout.strip().split('\n') if l]


def build_snapshots(lines, nb_villagers, pot_size, nb_refills, nb_fights):
    states = ['ready'] * nb_villagers
    pot = pot_size
    romans_defeated = 0
    total_romans = nb_villagers * nb_fights
    druid = 'sleeping'
    refills = nb_refills
    snapshots = []
    romans_history = [0]

    def snap(line):
        snapshots.append({
            'line':           line,
            'states':         states.copy(),
            'pot':            pot,
            'romans_defeated': romans_defeated,
            'total_romans':   total_romans,
            'druid':          druid,
            'refills':        refills,
            'romans_history': romans_history.copy(),
        })

    for line in lines:
        m = re.match(r'Villager (\d+): Going into battle!', line)
        if m:
            vid = int(m.group(1))
            if 0 <= vid < nb_villagers:
                states[vid] = 'battle'
            snap(line)
            continue

        m = re.match(r'Villager (\d+): I need a drink\.\.\. I see (\d+) servings left\.', line)
        if m:
            vid, pot = int(m.group(1)), int(m.group(2))
            if 0 <= vid < nb_villagers:
                states[vid] = 'waiting'
            snap(line)
            continue

        m = re.match(r'Villager (\d+): Hey Pano wake up!', line)
        if m:
            snap(line)
            continue

        m = re.match(r'Villager (\d+): Take that roman scum! Only (\d+) left\.', line)
        if m:
            vid = int(m.group(1))
            romans_defeated += 1
            romans_history.append(romans_defeated)
            if 0 <= vid < nb_villagers:
                states[vid] = 'fighting'
            snap(line)
            continue

        m = re.match(r"Villager (\d+): I'm going to sleep now\.", line)
        if m:
            vid = int(m.group(1))
            if 0 <= vid < nb_villagers:
                states[vid] = 'sleeping'
            snap(line)
            continue

        if re.match(r"Druid: I'm ready", line):
            snap(line)
            continue

        m = re.match(r'Druid: Ah! Yes.*can only make (\d+) more refills', line)
        if m:
            refills = int(m.group(1))
            druid = 'refilling'
            pot = pot_size
            snap(line)
            continue

        if re.match(r"Druid: I'm out of viscum", line):
            druid = 'done'
            snap(line)
            continue

    return snapshots


def style_ax(ax):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values():
        s.set_color(BORDER)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.title.set_color(ACCENT)
    ax.title.set_fontsize(10)
    ax.title.set_fontweight('bold')


def draw_villager_grid(ax, states, nb_villagers):
    ax.clear()
    style_ax(ax)
    ax.set_title('Villagers')
    ax.set_xticks([])
    ax.set_yticks([])

    display = min(nb_villagers, 600)
    cols = max(1, int(np.ceil(np.sqrt(display))))
    rows = max(1, int(np.ceil(display / cols)))

    grid = np.zeros((rows, cols, 3))
    for i in range(display):
        r, c = divmod(i, cols)
        grid[r, c] = matplotlib.colors.to_rgb(STATE_COLORS.get(states[i], STATE_COLORS['ready']))
    for i in range(display, rows * cols):
        r, c = divmod(i, cols)
        grid[r, c] = matplotlib.colors.to_rgb(BG)

    ax.imshow(grid, aspect='auto', interpolation='nearest')

    counts = {s: states.count(s) for s in STATE_COLORS}
    patches = [
        mpatches.Patch(color=STATE_COLORS[s], label=f'{s.capitalize()} ({counts[s]})')
        for s in STATE_COLORS if counts[s] > 0
    ]
    ax.legend(handles=patches, loc='lower right', fontsize=7,
              facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT, ncol=2, framealpha=0.9)


def draw_pot(ax, pot, pot_size, druid, refills):
    ax.clear()
    style_ax(ax)
    ax.set_title('Magic Pot')
    ax.set_xlim(0, 1)
    ax.set_ylim(-pot_size * 0.22, pot_size * 1.06)
    ax.set_xticks([])
    ticks = np.linspace(0, pot_size, min(6, pot_size + 1), dtype=int)
    ax.set_yticks(ticks)

    fill_color = (
        '#3fb950' if pot > pot_size * 0.5 else
        '#e3b341' if pot > pot_size * 0.2 else
        '#f85149'
    )
    ax.bar([0.5], [pot_size], width=0.55, color=DARK, zorder=1)
    ax.bar([0.5], [max(pot, 0)], width=0.55, color=fill_color, alpha=0.9, zorder=2)
    ax.text(0.5, max(pot / 2, pot_size * 0.08), f'{pot}/{pot_size}',
            ha='center', va='center', color='white', fontsize=11, fontweight='bold', zorder=3)

    druid_color = DRUID_COLORS.get(druid, DRUID_COLORS['sleeping'])
    ax.text(0.5, -pot_size * 0.09, f'Druid: {druid.upper()}',
            ha='center', va='center', color=druid_color, fontsize=9, fontweight='bold')
    ax.text(0.5, -pot_size * 0.175, f'Refills left: {refills}',
            ha='center', va='center', color=MUTED, fontsize=8)


def draw_romans(ax, romans_history, total_romans, current_event_idx, total_events):
    ax.clear()
    style_ax(ax)
    ax.set_title('Romans Defeated')
    ax.set_ylim(0, total_romans * 1.1)
    ax.set_xlim(0, max(total_events - 1, 1))
    ax.set_xlabel('Events', color=MUTED, fontsize=8)
    ax.set_ylabel('Defeated', color=MUTED, fontsize=8)

    full_x = list(range(len(romans_history)))
    ax.fill_between(full_x, romans_history, color='#f85149', alpha=0.25)
    ax.plot(full_x, romans_history, color='#f85149', linewidth=1.5)
    ax.axhline(total_romans, color=BORDER, linestyle='--', linewidth=1)
    ax.axvline(current_event_idx, color=ACCENT, linewidth=1, alpha=0.6)

    ax.text(total_events * 0.01, total_romans * 1.03, f'Goal: {total_romans}',
            color=MUTED, fontsize=7)

    current = romans_history[-1]
    pct = current / total_romans * 100 if total_romans else 0
    ax.text(0.98, 0.06, f'{current} / {total_romans}  ({pct:.1f}%)',
            transform=ax.transAxes, ha='right', color=TEXT, fontsize=9, fontweight='bold')


def draw_stats(ax, snap):
    ax.clear()
    style_ax(ax)
    ax.set_title('Live Stats')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    total_v  = len(snap['states'])
    rows = [
        ('In battle', snap['states'].count('battle'),   STATE_COLORS['battle']),
        ('Fighting',  snap['states'].count('fighting'), STATE_COLORS['fighting']),
        ('Waiting',   snap['states'].count('waiting'),  STATE_COLORS['waiting']),
        ('Ready',     snap['states'].count('ready'),    STATE_COLORS['ready']),
        ('Sleeping',  snap['states'].count('sleeping'), STATE_COLORS['sleeping']),
    ]

    ax.text(0.5, 0.96, 'Villagers', ha='center', va='top', color=ACCENT,
            fontsize=9, fontweight='bold', transform=ax.transAxes)

    for i, (label, count, color) in enumerate(rows):
        y = 0.84 - i * 0.145
        bar_w = (count / total_v) if total_v else 0
        ax.barh([y], [bar_w], height=0.09, left=0.30,
                color=color, alpha=0.85, transform=ax.transAxes)
        ax.text(0.28, y, label, ha='right', va='center',
                color=MUTED, fontsize=8, transform=ax.transAxes)
        ax.text(0.31 + bar_w + 0.01, y, str(count), ha='left', va='center',
                color=TEXT, fontsize=8, fontweight='bold', transform=ax.transAxes)

    last = snap['line']
    if len(last) > 50:
        last = last[:47] + '...'
    ax.text(0.5, 0.03, last, ha='center', va='bottom', color=MUTED,
            fontsize=6.5, style='italic', transform=ax.transAxes)


def style_btn(btn):
    btn.color = DARK
    btn.hovercolor = BORDER
    btn.label.set_color(TEXT)
    btn.label.set_fontsize(9)


def main():
    params = parse_args()
    nb_villagers, pot_size, nb_fights, nb_refills = params

    print("Running panoramix simulation...")
    lines = run_simulation(params)
    print(f"Captured {len(lines)} log lines, building snapshots...")

    snapshots = build_snapshots(lines, nb_villagers, pot_size, nb_refills, nb_fights)
    if not snapshots:
        print("No events captured.")
        sys.exit(1)

    n = len(snapshots)
    print(f"Parsed {n} events. Launching visualization...")

    fig = plt.figure(figsize=(15, 10), facecolor=BG)
    fig.suptitle(
        f'Panoramix Simulation  |  {nb_villagers} villagers'
        f'  ·  pot={pot_size}  ·  fights={nb_fights}  ·  refills={nb_refills}',
        color=TEXT, fontsize=12, fontweight='bold', y=0.988
    )

    gs = gridspec.GridSpec(
        2, 3, figure=fig,
        left=0.04, right=0.97, top=0.955, bottom=0.26,
        hspace=0.44, wspace=0.32
    )
    ax_grid   = fig.add_subplot(gs[0, 0:2])
    ax_pot    = fig.add_subplot(gs[0, 2])
    ax_romans = fig.add_subplot(gs[1, 0:2])
    ax_stats  = fig.add_subplot(gs[1, 2])

    ax_timeline = fig.add_axes([0.07, 0.175, 0.86, 0.024], facecolor=DARK)
    ax_timeline.spines['bottom'].set_color(BORDER)
    ax_timeline.spines['top'].set_color(BORDER)
    ax_timeline.spines['left'].set_color(BORDER)
    ax_timeline.spines['right'].set_color(BORDER)
    timeline = Slider(ax_timeline, '', 0, n - 1, valinit=0, valstep=1, color=ACCENT)
    timeline.track.set_facecolor(BORDER)
    timeline.label.set_color(TEXT)
    timeline.valtext.set_color(MUTED)
    timeline.valtext.set_fontsize(8)

    ax_start = fig.add_axes([0.07,  0.095, 0.065, 0.052], facecolor=DARK)
    ax_prev  = fig.add_axes([0.142, 0.095, 0.065, 0.052], facecolor=DARK)
    ax_play  = fig.add_axes([0.214, 0.095, 0.085, 0.052], facecolor=DARK)
    ax_next  = fig.add_axes([0.306, 0.095, 0.065, 0.052], facecolor=DARK)
    ax_end   = fig.add_axes([0.378, 0.095, 0.065, 0.052], facecolor=DARK)
    ax_speed = fig.add_axes([0.56,  0.108, 0.200, 0.024], facecolor=DARK)
    ax_speed.spines['bottom'].set_color(BORDER)
    ax_speed.spines['top'].set_color(BORDER)
    ax_speed.spines['left'].set_color(BORDER)
    ax_speed.spines['right'].set_color(BORDER)

    btn_start = Button(ax_start, '|◀')
    btn_prev  = Button(ax_prev,  '◀◀')
    btn_play  = Button(ax_play,  '▶ Play')
    btn_next  = Button(ax_next,  '▶▶')
    btn_end   = Button(ax_end,   '▶|')
    speed_sl  = Slider(ax_speed, 'Speed', 1, 10, valinit=5, valstep=1, color=ACCENT)

    for btn in [btn_start, btn_prev, btn_play, btn_next, btn_end]:
        style_btn(btn)
    speed_sl.track.set_facecolor(BORDER)
    speed_sl.label.set_color(TEXT)
    speed_sl.label.set_fontsize(9)
    speed_sl.valtext.set_color(MUTED)
    speed_sl.valtext.set_fontsize(8)

    fig.text(0.50, 0.083, 'Speed', ha='center', color=MUTED, fontsize=8)

    event_label = fig.text(0.5, 0.022, '', ha='center', color=MUTED, fontsize=8)

    state = {'idx': 0, 'playing': False}

    def render(idx):
        idx = int(np.clip(idx, 0, n - 1))
        state['idx'] = idx
        snap = snapshots[idx]
        draw_villager_grid(ax_grid, snap['states'], nb_villagers)
        draw_pot(ax_pot, snap['pot'], pot_size, snap['druid'], snap['refills'])
        draw_romans(ax_romans, snap['romans_history'], snap['total_romans'], idx, n)
        draw_stats(ax_stats, snap)

        timeline.eventson = False
        timeline.set_val(idx)
        timeline.eventson = True

        short = snap['line'] if len(snap['line']) <= 80 else snap['line'][:77] + '...'
        event_label.set_text(f'Event {idx + 1} / {n}   —   {short}')
        fig.canvas.draw_idle()

    def on_timeline(val):
        render(int(val))

    def on_start(_):
        stop_playing()
        render(0)

    def on_prev(_):
        stop_playing()
        render(state['idx'] - 1)

    def on_next(_):
        stop_playing()
        render(state['idx'] + 1)

    def on_end(_):
        stop_playing()
        render(n - 1)

    def stop_playing():
        if state['playing']:
            timer.stop()
            state['playing'] = False
            btn_play.label.set_text('▶ Play')

    def on_play(_):
        if state['playing']:
            stop_playing()
        else:
            if state['idx'] >= n - 1:
                render(0)
            state['playing'] = True
            btn_play.label.set_text('⏸ Pause')
            timer.start()

    def auto_step():
        if not state['playing']:
            return
        nxt = state['idx'] + 1
        if nxt >= n:
            stop_playing()
            return
        render(nxt)

    def on_speed(val):
        ms = int(600 / int(val))
        if state['playing']:
            timer.stop()
            timer.interval = ms
            timer.start()
        else:
            timer.interval = ms

    timer = fig.canvas.new_timer(interval=120)
    timer.add_callback(auto_step)

    timeline.on_changed(on_timeline)
    btn_start.on_clicked(on_start)
    btn_prev.on_clicked(on_prev)
    btn_play.on_clicked(on_play)
    btn_next.on_clicked(on_next)
    btn_end.on_clicked(on_end)
    speed_sl.on_changed(on_speed)

    render(0)
    plt.show()
    timer.stop()


if __name__ == '__main__':
    main()
