"""Validações e conversões puras dos dados de análise de solo."""
from datetime import date, datetime

def validar_data_laudo(data_texto, hoje=None):
    """Valida data do laudo e evita gerar recomendação atual com análise antiga."""
    if not data_texto:
        return "Informe a data da coleta da análise de solo."
    try:
        coleta = datetime.strptime(data_texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "A data da coleta é inválida. Selecione uma data válida."
    hoje = hoje or date.today()
    if coleta > hoje:
        return "A data da coleta não pode estar no futuro. Confira o laudo."
    if (hoje - coleta).days > 730:
        return ("Este laudo tem mais de dois anos. Para uma recomendação de campo, "
                "obtenha uma análise de solo atualizada; o AgroCalc não calculou a dose.")
    return None


def normalizar_unidades_solo(valores, unidades):
    """Converte unidades explicitamente selecionadas para as unidades internas.

    Ca, Mg, K, H+Al e CTC ficam em cmolc/dm³; P em mg/dm³; argila em %.
    Não deduz unidades a partir do tamanho dos números.
    """
    conversoes = []
    divisores = {
        "ca": {"mg/dm3": (200.4, "mg/dm³ → cmolc/dm³"), "mmolc/dm3": (10.0, "mmolc/dm³ → cmolc/dm³")},
        "mg": {"mg/dm3": (121.5, "mg/dm³ → cmolc/dm³"), "mmolc/dm3": (10.0, "mmolc/dm³ → cmolc/dm³")},
        "k": {"mg/dm3": (391.0, "mg/dm³ ÷ 391 → cmolc/dm³")},
        "h_al": {"mmolc/dm3": (10.0, "mmolc/dm³ → cmolc/dm³")},
        "ctc_t": {"mmolc/dm3": (10.0, "mmolc/dm³ → cmolc/dm³")},
        "argila": {"g/kg": (10.0, "g/kg → %")},
    }
    permitidas = {
        "ca": {"cmolc/dm3", "mg/dm3", "mmolc/dm3"}, "mg": {"cmolc/dm3", "mg/dm3", "mmolc/dm3"},
        "k": {"cmolc/dm3", "mg/dm3"}, "h_al": {"cmolc/dm3", "mmolc/dm3"},
        "ctc_t": {"cmolc/dm3", "mmolc/dm3"}, "argila": {"%", "g/kg"},
        "p": {"mg/dm3", "ppm"}, "ph": {"ph"}, "v1_atual": {"%"},
    }
    for campo, opcoes_validas in permitidas.items():
        unidade = unidades.get(campo, next(iter(opcoes_validas)))
        if unidade not in opcoes_validas:
            raise ValueError(f"Unidade inválida para {campo}")
        if valores.get(campo) is not None and unidade in divisores.get(campo, {}):
            divisor, descricao = divisores[campo][unidade]
            valores[campo] = valores[campo] / divisor
            conversoes.append(f"{campo.replace('_', ' ').upper()}: {descricao}")
    return conversoes



def calcular_dose_fertilizante(alvo_kg_ha, teor_percentual, area_ha):
    """Converte uma meta técnica de nutriente em dose de produto comercial.

    A meta deve ter sido definida pelo agrônomo com base em recomendação técnica
    local; esta função não interpreta sozinha a classe de fertilidade do solo.
    """
    import math
    alvo = float(alvo_kg_ha)
    teor = float(teor_percentual)
    area = float(area_ha)
    if not all(math.isfinite(v) for v in (alvo, teor, area)):
        raise ValueError("Use valores numéricos finitos.")
    if alvo < 0 or alvo > 1000:
        raise ValueError("A meta de nutriente deve estar entre 0 e 1000 kg/ha.")
    if not 0 <= teor <= 100:
        raise ValueError("O teor do fertilizante deve estar entre 0 e 100%.")
    if area <= 0:
        raise ValueError("A área deve ser maior que zero.")
    if alvo == 0:
        return 0.0, 0.0
    if teor <= 0:
        raise ValueError("O fertilizante selecionado não contém o nutriente solicitado.")
    dose_kg_ha = alvo / (teor / 100.0)
    return dose_kg_ha, dose_kg_ha * area
