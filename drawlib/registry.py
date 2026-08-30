"""The element registry.

Kept in its own module so ``scene`` and ``elements`` can both import it
without a circular import.
"""

REGISTRY: dict = {}

# Arabic names accepted in scene files alongside the English ones.
ALIASES: dict[str, str] = {
    "دائرة": "circle", "بيضاوي": "ellipse", "مستطيل": "rect",
    "مضلع": "polygon", "نجمة": "star", "كتلة": "blob", "مسار": "path",
    "خط": "line", "نص": "text",
    "كائن": "creature", "مصباح": "lamp", "نبتة": "plant", "وسادة": "cushion",
    "كتاب": "book", "كوب": "mug", "شجرة": "tree", "سحابة": "cloud",
    "جرم": "celestial", "بيت": "house",
    "مجموعة": "group", "تكرار": "repeat",
}


def element(name: str):
    """Register an element function under ``name``."""
    def wrap(fn):
        REGISTRY[name] = fn
        return fn
    return wrap
