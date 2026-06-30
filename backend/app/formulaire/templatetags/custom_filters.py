from django import template

register = template.Library()

@register.filter
def get_placeholder(placeholders_dict, depth):
    """
    Récupère le placeholder pour une profondeur donnée.

    Usage dans le template:
    {{ main_skills_placeholders.bullet|get_placeholder:depth }}
    """
    if not isinstance(placeholders_dict, dict):
        return "Item"

    return placeholders_dict.get(depth, "Item")

@register.filter
def get_item(items_list, index):
    """
    Récupère un élément d'une liste par index.

    Usage dans le template:
    {{ xp_pro_placeholders|get_item:depth }}
    """
    if not isinstance(items_list, list):
        return None

    try:
        index = int(index)
        if 0 <= index < len(items_list):
            return items_list[index]
    except (ValueError, TypeError):
        pass

    return None
