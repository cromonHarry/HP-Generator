
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
import math

def draw_ap_model(ap_model):
    if hasattr(ap_model, "to_json"):
        data = ap_model.to_json()
    elif isinstance(ap_model, dict):
        data = ap_model
    else:
        data = getattr(ap_model, "__dict__", {})

    mt_minus1 = data.get('mt_minus1', {})
    mt = data.get('mt', {})
    mt_plus1 = data.get('mt_plus1', {})

    left_x, center_x, right_x = 0.15, 0.5, 0.85
    max_count = max(len(mt_minus1), len(mt), len(mt_plus1), 1)
    height = 0.7
    y_step = height / (max_count + 1)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    def draw_node(x, y, text, radius=0.06):
        circ = Circle((x, y), radius=radius, edgecolor='#333', facecolor='#fff', linewidth=1.2, zorder=2)
        ax.add_patch(circ)
        lines = wrap_text(text, max_chars=20)
        ax.text(x, y, '\\n'.join(lines), ha='center', va='center', fontsize=9, zorder=3)

    def wrap_text(s, max_chars=20):
        s = str(s)
        s = s.replace('\\n', ' ')
        words = s.split(' ')
        lines = []
        cur = ''
        for w in words:
            if len(cur) + len(w) + 1 <= max_chars:
                cur = (cur + ' ' + w).strip()
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    positions = {}
    def draw_column(items, x):
        positions_local = {}
        if not items:
            return positions_local
        keys = list(items.keys())
        count = len(keys)
        for i, k in enumerate(keys):
            y = 0.9 - (i+1) * y_step
            val = items.get(k, '')
            draw_node(x, y, k + '\\n' + str(val))
            positions_local[k] = (x, y)
        return positions_local

    pos_m1 = draw_column(mt_minus1, left_x)
    pos_m  = draw_column(mt, center_x)
    pos_p1 = draw_column(mt_plus1, right_x)

    def draw_arrow(p_from, p_to):
        if not p_from or not p_to:
            return
        x1, y1 = p_from
        x2, y2 = p_to
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        r = 0.06
        start_x = x1 + (dx/dist) * r
        start_y = y1 + (dy/dist) * r
        end_x = x2 - (dx/dist) * r
        end_y = y2 - (dy/dist) * r
        arrow = FancyArrowPatch((start_x, start_y), (end_x, end_y), arrowstyle='->', mutation_scale=15, color='#555', linewidth=1.2, zorder=1)
        ax.add_patch(arrow)

    for k in pos_m:
        if k in pos_m1:
            draw_arrow(pos_m1[k], pos_m[k])
        if k in pos_p1:
            draw_arrow(pos_m[k], pos_p1[k])
    for k in pos_m1:
        if k in pos_p1:
            draw_arrow(pos_m1[k], pos_p1[k])

    fig.tight_layout()
    return fig
