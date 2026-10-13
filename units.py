KG_PER_LB = 1 / 2.20462
LB_PER_KG = 2.20462


def pounds_to_kg(pounds):
    return float(pounds) * KG_PER_LB


def kg_to_pounds(kg):
    return float(kg) * LB_PER_KG


def to_kg(weight, unit):
    if unit == "lb":
        return pounds_to_kg(weight)
    return float(weight)


def from_kg(weight_kg, unit):
    if unit == "lb":
        return kg_to_pounds(weight_kg)
    return float(weight_kg)


def weight_step(unit):
    return 2.5 if unit == "lb" else 1.0


def weight_label(unit):
    return f"Weight ({unit})"
