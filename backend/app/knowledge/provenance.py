"""Provenance and semantic classification constants (Foundation skeleton).

Subetapa B will bind these to persistence and validation rules.
Inferências NÃO podem ser promovidas a fato automaticamente.
"""

from __future__ import annotations

from enum import Enum


class ClaimType(str, Enum):
    FATO_VERIFICADO = "fato_verificado"
    DECLARACAO = "declaracao"
    INFERENCIA = "inferencia"
    HIPOTESE = "hipotese"
    PREVISAO = "previsao"
    DESCONHECIDO = "desconhecido"


class VerificationStatus(str, Enum):
    NAO_VERIFICADO = "nao_verificado"
    EM_VERIFICACAO = "em_verificacao"
    VERIFICADO = "verificado"
    CONTESTADO = "contestado"
    INVALIDO = "invalido"


NON_FACT_TYPES = {
    ClaimType.DECLARACAO,
    ClaimType.INFERENCIA,
    ClaimType.HIPOTESE,
    ClaimType.PREVISAO,
    ClaimType.DESCONHECIDO,
}
