"""صفحة تلوين: ثعلب صغير يقرأ كتاباً على وسادة.

يُنتج صورة واحدة فيها:
  - نسخة ملوّنة صغيرة في الأعلى (مرجع الألوان)
  - نسخة بالخطوط فقط في الأسفل (للتلوين)

التشغيل:  python3 fox_coloring_page.py
"""

import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D


# ------------------------------------------------------------ أدوات هندسية

def smooth_closed(points, tension=1.0):
    """يحوّل نقاطاً قليلة إلى شكل عضوي مغلق ناعم (Catmull-Rom -> Bezier)."""
    n = len(points)
    verts, codes = [points[0]], [Path.MOVETO]
    for i in range(n):
        p0, p1 = points[(i - 1) % n], points[i]
        p2, p3 = points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension,
              p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension,
              p2[1] - (p3[1] - p1[1]) / 6 * tension)
        verts += [c1, c2, p2]
        codes += [Path.CURVE4] * 3
    return Path(verts, codes)


def polygon(points):
    return Path(list(points) + [points[0]],
                [Path.MOVETO] + [Path.LINETO] * len(points))


def ellipse(cx, cy, w, h):
    return Path.circle().transformed(
        Affine2D().scale(w / 2, h / 2).translate(cx, cy))


def star(cx, cy, r, tips=5, inner=0.42, rot=90):
    pts = []
    for i in range(tips * 2):
        ang = math.radians(rot + i * 180 / tips)
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return polygon(pts)


def bezier(p0, p1, p2, p3, n=40):
    """نقاط على منحنى بيزييه تكعيبي."""
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0]
                    + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1]
                    + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def ribbon(spine, width_at):
    """شريط سميك يتبع منحنى، بعرض متغيّر — مناسب لذيل الثعلب."""
    left, right = [], []
    n = len(spine) - 1
    for i, (x, y) in enumerate(spine):
        j0, j1 = max(0, i - 1), min(n, i + 1)
        dx = spine[j1][0] - spine[j0][0]
        dy = spine[j1][1] - spine[j0][1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        w = width_at(i / n) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return smooth_closed(left + right[::-1], tension=0.55)


# --------------------------------------------------------------- لوح الرسم

class Canvas:
    """يرسم نفس المشهد إمّا ملوّناً أو بالخطوط فقط."""

    def __init__(self, ax, transform, colored, lw):
        self.ax = ax
        self.tr = transform + ax.transData
        self.colored = colored
        self.lw = lw

    def shape(self, path, color, lw=1.0, z=1):
        fill = color if self.colored else "white"
        self.ax.add_patch(PathPatch(
            path, facecolor=fill, edgecolor="black", linewidth=self.lw * lw,
            transform=self.tr, zorder=z, joinstyle="round", capstyle="round"))

    def ink(self, path, z=30):
        """تفصيل أسود دائماً: عين، أنف."""
        self.ax.add_patch(PathPatch(path, facecolor="black", edgecolor="none",
                                    transform=self.tr, zorder=z))

    def stroke(self, pts, lw=1.0, z=30, curve=False):
        codes = ([Path.MOVETO] + [Path.CURVE4] * 3 if curve
                 else [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1))
        self.ax.add_patch(PathPatch(
            Path(pts, codes), facecolor="none", edgecolor="black",
            linewidth=self.lw * lw, transform=self.tr, zorder=z,
            capstyle="round"))


# ------------------------------------------------------------------ الألوان
ORANGE = "#F4802B"
CREAM = "#FFF1E0"
PINK = "#F6A7A1"
RED = "#E1362F"
BROWN = "#8A5A2B"
YELLOW = "#FBCF4B"
GREEN = "#3FA34D"
BLUE = "#2E7BC4"
TERRA = "#C87941"
WHITE = "#FFFFFF"


# ------------------------------------------------------------------ المشهد

def draw_scene(c):
    """المشهد في إحداثيات محلية ≈ x:0..128 و y:0..100."""

    # ----- النجوم
    for cx, cy, r in [(8, 54, 6), (16, 71, 5), (25, 87, 6),
                      (85, 101, 6), (112, 60, 5.5)]:
        c.shape(star(cx, cy, r), YELLOW, z=0)

    # ----- المصباح
    c.shape(ellipse(97, 12, 15, 5), WHITE, z=1)
    c.shape(polygon([(95.7, 12), (98.3, 12), (98.3, 78), (95.7, 78)]), BROWN, z=1)
    c.shape(polygon([(86, 78), (110, 78), (105, 96), (91, 96)]), YELLOW, z=2)
    c.stroke([(93, 76), (93, 68)], z=3)
    c.shape(ellipse(93, 66, 3.4, 3.4), WHITE, z=3)

    # ----- النبتة
    for dx, tip in [(-6, (105, 42)), (0, (115, 47)), (6, (125, 42))]:
        c.shape(smooth_closed([(115, 17), (110 + dx, 30), tip, (120 + dx, 30)],
                              tension=0.85), GREEN, z=1)
    c.shape(polygon([(106, 17), (124, 17), (121, 2), (109, 2)]), TERRA, z=2)

    # ----- الوسادة
    c.shape(ellipse(50, 13, 96, 30), RED, z=3)

    # ----- الذيل
    c.shape(smooth_closed([(38, 21), (26, 14), (12, 15), (4, 25), (9, 37),
                           (22, 41), (34, 34)], tension=1.0), ORANGE, z=4)
    c.shape(smooth_closed([(3, 26), (9, 37), (19, 33), (16, 20), (6, 17)],
                          tension=0.85), CREAM, z=5)

    # ----- الجسم
    c.shape(smooth_closed([(52, 17), (68, 21), (73, 36), (66, 49),
                           (52, 54), (38, 49), (32, 36), (37, 21)],
                          tension=0.9), ORANGE, z=6)
    c.shape(smooth_closed([(52, 19), (62, 25), (60, 37), (52, 42),
                           (44, 37), (42, 25)], tension=0.9), CREAM, z=7)

    # ----- الأقدام
    c.shape(ellipse(60, 16, 15, 10), BROWN, z=8)
    c.shape(ellipse(75, 22, 14, 10), BROWN, z=8)

    # ----- الأذنان
    c.shape(smooth_closed([(38, 74), (33, 93), (51, 81)], tension=0.45), ORANGE, z=12)
    c.shape(smooth_closed([(64, 81), (75, 95), (77, 74)], tension=0.45), ORANGE, z=12)
    c.shape(smooth_closed([(41, 77), (38, 87), (47, 80)], tension=0.4), CREAM, z=13)
    c.shape(smooth_closed([(67, 81), (72, 89), (73, 78)], tension=0.4), CREAM, z=13)

    # ----- الرأس
    c.shape(smooth_closed([(55, 48), (71, 53), (77, 66), (71, 80),
                           (55, 85), (39, 80), (33, 66), (39, 53)],
                          tension=0.9), ORANGE, z=14)
    # خصلة الجبين
    c.shape(smooth_closed([(43, 79), (47, 86), (51, 80), (56, 84), (59, 78)],
                          tension=0.6), ORANGE, z=15)
    # الكمّامة
    c.shape(smooth_closed([(55, 51), (67, 57), (65, 66), (55, 70),
                           (45, 66), (43, 57)], tension=0.9), CREAM, z=15)
    # الخدود
    c.shape(ellipse(39, 62, 9, 5), PINK, z=16)
    c.shape(ellipse(71, 62, 9, 5), PINK, z=16)
    # العينان والأنف والابتسامة
    c.ink(ellipse(49, 67, 6.0, 6.8), z=17)
    c.ink(ellipse(61, 67, 6.0, 6.8), z=17)
    c.ink(ellipse(55, 60, 4.6, 3.6), z=17)
    c.stroke([(55, 58.5), (52, 55), (55, 52.5), (58.5, 55)], lw=0.8, z=17, curve=True)

    # ----- الكتاب المفتوح
    c.shape(polygon([(58, 27), (41, 35), (41, 43), (58, 35)]), WHITE, z=20)
    c.shape(polygon([(58, 27), (77, 37), (77, 45), (58, 35)]), WHITE, z=20)
    c.shape(polygon([(60, 29), (75.5, 37.4), (75.5, 44), (60, 35.6)]), BROWN, z=21)
    c.shape(polygon([(63, 32.5), (71, 36.8), (71, 41), (63, 36.7)]), GREEN, z=22)
    for k in (1, 2):
        c.stroke([(54, 30.5 + 2 * k), (44, 35 + 2 * k)], lw=0.6, z=21)

    # ----- الكفّان يمسكان الكتاب
    c.shape(ellipse(43, 39, 12, 9), ORANGE, z=23)
    c.shape(ellipse(78, 42, 11, 9), ORANGE, z=23)

    # ----- الكوب
    c.shape(ellipse(29, 7, 10, 10), WHITE, z=25)
    c.shape(smooth_closed([(13, 13), (25, 13), (24, 1), (14, 1)],
                          tension=0.35), BLUE, z=26)
    c.shape(ellipse(29, 7, 4.5, 4.5), WHITE, z=27)
    c.shape(star(19, 7, 3.4), WHITE, z=28)


# ------------------------------------------------------------------ التركيب

def render(out="fox_coloring_page.png"):
    fig, ax = plt.subplots(figsize=(7.5, 10), dpi=200)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 200)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(0, 0, 1, 1)

    # النسخة الملوّنة الصغيرة (أعلى اليمين)
    draw_scene(Canvas(ax, Affine2D().scale(0.42).translate(80, 150),
                      colored=True, lw=1.5))
    # نسخة الخطوط الكبيرة (الأسفل)
    draw_scene(Canvas(ax, Affine2D().scale(1.02).translate(11, 10),
                      colored=False, lw=2.6))

    fig.savefig(out, facecolor="white")
    plt.close(fig)
    print("تم الحفظ:", out)


if __name__ == "__main__":
    render()
