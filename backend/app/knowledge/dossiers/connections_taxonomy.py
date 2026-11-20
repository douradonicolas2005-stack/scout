from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional


@dataclass(frozen=True)
class RelationTypeSpec:
    id: str
    category: str
    name: str
    description: str
    directionality: str  # directed|undirected
    from_entity_types: FrozenSet[str]
    to_entity_types: FrozenSet[str]
    status_mvp: str  # approved|requires_review|blocked_by_model|deferred
    inverse_label: Optional[str] = None
    symmetric_label: Optional[str] = None
    inverse_type_id: Optional[str] = None
    notes: Optional[str] = None


SPECS: Dict[str, RelationTypeSpec] = {}


def _reg(spec: RelationTypeSpec) -> None:
    SPECS[spec.id] = spec


# Societária
_reg(RelationTypeSpec(
    id="corp.shareholder_of", category="Societária", name="Acionista/Sócio de",
    description="Participação societária declarada/observada.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como acionista",
))
_reg(RelationTypeSpec(
    id="corp.parent_company_of", category="Societária", name="Controladora de",
    description="Relação de controle/controladora sobre controlada no escopo registrado.",
    directionality="directed",
    from_entity_types=frozenset({"company", "economic_group", "institution"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Controlada por",
))
_reg(RelationTypeSpec(
    id="corp.beneficial_owner_of", category="Societária", name="Beneficiário final de",
    description="UBO distinto de titular formal/registral e de participação direta/controle indireto.",
    directionality="directed",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="requires_review", inverse_label="Tem como beneficiário final",
    notes="Não operacional no MVP; exige confirmação humana explícita de critérios.",
))
_reg(RelationTypeSpec(
    id="corp.partner_in_vehicle", category="Societária", name="Coparticipante em veículo (não operacional)",
    description="Coparticipação sem veículo representável adequadamente.",
    directionality="undirected",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="blocked_by_model", symmetric_label="Coparticipante",
    notes="Não habilitado no MVP (veículo comum não representável).",
))

# Executiva
_reg(RelationTypeSpec(
    id="exec.director_of", category="Executiva", name="Diretor(a) de",
    description="Pessoa no exercício de função de direção em organização.",
    directionality="directed",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como diretor(a)",
))
_reg(RelationTypeSpec(
    id="exec.officer_of", category="Executiva", name="Executivo(a)/Officer de",
    description="Pessoa em vínculo executivo/oficial junto à organização.",
    directionality="directed",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como executivo(a)",
))
_reg(RelationTypeSpec(
    id="exec.board_member_of", category="Executiva", name="Membro de conselho de",
    description="Pessoa membro de conselho/órgão colegiado da organização.",
    directionality="directed",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como conselheiro(a)",
))
_reg(RelationTypeSpec(
    id="exec.advisor_to", category="Executiva", name="Assessor(a) de",
    description="Relação profissional de aconselhamento/assessoria, sem presumir vínculo empregatício/societário/cargo executivo/exclusividade.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Assessorado(a) por",
))
_reg(RelationTypeSpec(
    id="exec.employee_of", category="Executiva", name="Colaborador(a) de",
    description="Pessoa em vínculo de colaboração/emprego com organização.",
    directionality="directed",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como colaborador(a)",
))

# Familiar
_reg(RelationTypeSpec(
    id="fam.spouse_of", category="Familiar", name="Cônjuge/companheiro(a) de",
    description="Vínculo conjugal/união estável entre pessoas.",
    directionality="undirected",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"person"}),
    status_mvp="approved", symmetric_label="Cônjuge/companheiro(a) de",
))
_reg(RelationTypeSpec(
    id="fam.parent_of", category="Familiar", name="Pai/mãe/responsável de",
    description="Relação parental/responsabilidade entre pessoas.",
    directionality="directed",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"person"}),
    status_mvp="approved", inverse_label="Filho(a)/dependente de",
))
_reg(RelationTypeSpec(
    id="fam.sibling_of", category="Familiar", name="Irmão(ã) de",
    description="Relação de irmandade entre pessoas.",
    directionality="undirected",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"person"}),
    status_mvp="approved", symmetric_label="Irmão(ã) de",
))
_reg(RelationTypeSpec(
    id="fam.relative_of", category="Familiar", name="Parente de",
    description="Parentesco entre pessoas não especificado por tipos anteriores.",
    directionality="undirected",
    from_entity_types=frozenset({"person"}),
    to_entity_types=frozenset({"person"}),
    status_mvp="approved", symmetric_label="Parente de",
))

# Empresarial
_reg(RelationTypeSpec(
    id="biz.supplier_to", category="Empresarial", name="Fornecedor de",
    description="Fornecedor de bens/serviços.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="É cliente de", inverse_type_id="biz.customer_of",
))
_reg(RelationTypeSpec(
    id="biz.customer_of", category="Empresarial", name="Cliente de",
    description="Cliente/contratante.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="É fornecedor de", inverse_type_id="biz.supplier_to",
))
_reg(RelationTypeSpec(
    id="biz.contractor_of", category="Empresarial", name="Contratado/prestador de",
    description="Prestador/contratado.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Contrata",
))
_reg(RelationTypeSpec(
    id="biz.commercial_partner_of", category="Empresarial", name="Parceiro comercial de",
    description="Parceria comercial simétrica.",
    directionality="undirected",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", symmetric_label="Parceiro comercial de",
))

# Institucional
_reg(RelationTypeSpec(
    id="inst.member_of", category="Institucional", name="Membro de",
    description="Membro de instituição/organização/rede representada como entidade D1.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"institution", "company", "economic_group"}),
    status_mvp="approved", inverse_label="Tem como membro",
))
_reg(RelationTypeSpec(
    id="inst.regulated_by", category="Institucional", name="Regulado por",
    description="Sujeição à regulação/supervisão por entidade reguladora.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"institution"}),
    status_mvp="approved", inverse_label="Regula",
))
_reg(RelationTypeSpec(
    id="inst.representative_of", category="Institucional", name="Representante de",
    description="Representação/mandato.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Representado(a) por",
))
_reg(RelationTypeSpec(
    id="inst.partner_of", category="Institucional", name="Parceiro institucional de",
    description="Parceria institucional simétrica.",
    directionality="undirected",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="approved", symmetric_label="Parceiro institucional de",
))

# Patrimonial
_reg(RelationTypeSpec(
    id="asset.owner_of", category="Patrimonial", name="Proprietário de (não operacional)",
    description="Titularidade de ativo (não habilitado no MVP).",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset(),
    status_mvp="blocked_by_model", inverse_label="Tem como proprietário",
    notes="Não habilitado no MVP (sem tipo de entidade ativo).",
))
_reg(RelationTypeSpec(
    id="asset.trustee_of", category="Patrimonial", name="Trustee/administrador fiduciário de",
    description="Trustee de estrutura/veículo representado como entidade D1.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "institution"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como trustee",
))
_reg(RelationTypeSpec(
    id="asset.beneficiary_of", category="Patrimonial", name="Beneficiário de (estrutura/veículo)",
    description="Beneficiário de estrutura/veículo/patrimônio representado como entidade D1.",
    directionality="directed",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"company", "economic_group", "institution"}),
    status_mvp="approved", inverse_label="Tem como beneficiário",
))
_reg(RelationTypeSpec(
    id="asset.co_owner_of", category="Patrimonial", name="Coproprietário de (não operacional)",
    description="Copropriedade (não habilitada no MVP).",
    directionality="undirected",
    from_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    to_entity_types=frozenset({"person", "company", "economic_group", "institution"}),
    status_mvp="blocked_by_model", symmetric_label="Coproprietário de",
    notes="Não habilitado no MVP (ativo/contexto comum não representável).",
))

# Basic consistency check
for _id, _s in SPECS.items():
    if _s.inverse_type_id:
        inv = SPECS.get(_s.inverse_type_id)
        if inv is None or inv.inverse_type_id != _id:
            raise RuntimeError(f"Inconsistent inverse pair: {_id}")
