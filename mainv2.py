from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
from typing import Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# TOGGLE
# ─────────────────────────────────────────────────────────────────────────────
USE_DUMMY_DATA = True

# ─────────────────────────────────────────────────────────────────────────────
# ORACLE CONNECTION  (commented out)
# ─────────────────────────────────────────────────────────────────────────────
# import cx_Oracle
# DB_DSN  = "your_host:1521/your_service"
# DB_USER = "your_user"
# DB_PASS = "your_password"
# def get_connection():
#     return cx_Oracle.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

# ─────────────────────────────────────────────────────────────────────────────
# ORACLE FUNCTIONS  (commented out — see main1_sync.py for full stubs)
# ─────────────────────────────────────────────────────────────────────────────
# def db_get_applications() -> list[str]: ...
# def db_get_datamodels(application: str) -> list[dict]: ...
# def db_get_fields(application: str, model_name: str) -> list[dict]: ...
# def db_get_all_edges_for_field(application: str, start_path: str) -> list[dict]: ...
# def db_get_datasource_fields(application: str, datasource: str) -> list[dict]: ...
# def db_get_all_datasources(application: str) -> list[str]: ...

# ─────────────────────────────────────────────────────────────────────────────
# DUMMY DATA  —  uses the exact reference JSON from the spec
# ─────────────────────────────────────────────────────────────────────────────

_DUMMY_APPLICATIONS = ["AXIOM_CRR3", "FINREP", "COREP"]

_DUMMY_DATAMODELS = {
    "AXIOM_CRR3": [
        {
            "application":     "AXIOM_CRR3",
            "vdm_id":          "VDM_001",
            "model_name":      "pr_DATA_ENRICHMENT_CRR3",
            "model_version":   "1.0.0",
            "base_path":       "pr_DATA_ENRICHMENT_CRR3/1_0_0_0"
        },
        {
            "application":     "AXIOM_CRR3",
            "vdm_id":          "VDM_002",
            "model_name":      "pr_DATA_CRR3",
            "model_version":   "1.0.0",
            "base_path":       "pr_DATA_CRR3/1_0_0_0"
        },
    ],
    "FINREP": [
        {
            "application":     "FINREP",
            "vdm_id":          "VDM_F01",
            "model_name":      "pr_DATA_ENRICHMENT_FINREP",
            "model_version":   "2.1.0",
            "base_path":       "pr_DATA_ENRICHMENT_FINREP/2_1_0"
        },
    ],
    "COREP": [
        {
            "application":     "COREP",
            "vdm_id":          "VDM_C01",
            "model_name":      "pr_DATA_COREP_OWNFUNDS",
            "model_version":   "3.0.0",
            "base_path":       "pr_DATA_COREP_OWNFUNDS/3_0_0"
        },
    ],
}

_DUMMY_FIELDS = {
    ("AXIOM_CRR3", "pr_DATA_ENRICHMENT_CRR3"): [
        {"vdm_id":"VDM_001","model_name":"pr_DATA_ENRICHMENT_CRR3","field_name":"fair_v1",
         "field_path":"pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_CCR9_REPORTING_INPUTS/Aggregation.fair_v1",
         "field_type":"ModifyModel"},
        {"vdm_id":"VDM_001","model_name":"pr_DATA_ENRICHMENT_CRR3","field_name":"PrchRecFlg",
         "field_path":"pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_SEC_C13_01_MAX_SUM/Aggregation.PrchRecFlg",
         "field_type":"ModifyModel"},
        {"vdm_id":"VDM_001","model_name":"pr_DATA_ENRICHMENT_CRR3","field_name":"SecId",
         "field_path":"pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_SEC_C13_01_MAX_SUM/Aggregation.SecId",
         "field_type":"ModifyModel"},
    ],
    ("AXIOM_CRR3", "pr_DATA_CRR3"): [
        {"vdm_id":"VDM_002","model_name":"pr_DATA_CRR3","field_name":"PrchRecFlg",
         "field_path":"pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_CR_SEC/root.PrchRecFlg",
         "field_type":"DataSource"},
    ],
    ("FINREP", "pr_DATA_ENRICHMENT_FINREP"): [
        {"vdm_id":"VDM_F01","model_name":"pr_DATA_ENRICHMENT_FINREP","field_name":"GrossCarryAmt",
         "field_path":"pr_DATA_ENRICHMENT_FINREP/2_1_0/ModifyModel/dmm_FINREP_F01/Aggregation.GrossCarryAmt",
         "field_type":"ModifyModel"},
    ],
    ("COREP", "pr_DATA_COREP_OWNFUNDS"): [
        {"vdm_id":"VDM_C01","model_name":"pr_DATA_COREP_OWNFUNDS","field_name":"CET1_Capital",
         "field_path":"pr_DATA_COREP_OWNFUNDS/3_0_0/Aggregation/agg_OWNFUNDS_TOTAL/Aggregation.CET1_Capital",
         "field_type":"Aggregation"},
    ],
}

# All lineage edges — conditions stored as JSON strings (mimics CLOB)
_DUMMY_EDGES: list[dict] = [

    # ── fair_v1 chain ─────────────────────────────────────────────────────────
    # Exact reference data from spec
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_CCR9_FLOW_REPORTING_INPUTS/Aggregation.fair_v1",
        "parent_objType": "Aggregation",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_CCR9_REPORTING_INPUTS/Aggregation.fair_v1",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": []
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_CCR9_FLOW_INT_JOIN/Aggregation.fair_v1",
        "parent_objType": "ModifyModel",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_CCR9_FLOW_REPORTING_INPUTS/Aggregation.fair_v1",
        "child_objType": "Aggregation",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<dm1.Aggregation->enm_crdt_drvtv_prdct_typ>> IS NOT NULL"],
            "joiningConditions": [],
            "columnLevelConditions": "MAX (<<dm1.Aggregation->fair_v1>>)"
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_CCR9_FLOW_DATA_REDUCTION/Aggregation.fair_v1",
        "parent_objType": "Aggregation",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_CCR9_FLOW_INT_JOIN/Aggregation.fair_v1",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": []
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_TRADE_CCR9_EXT_DERV_TYPE_JOIN/root.MTMRpt",
        "parent_objType": "ModifyModel",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_CCR9_FLOW_DATA_REDUCTION/Aggregation.fair_v1",
        "child_objType": "Aggregation",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<dm1.crdt_deriv_prd_typ->crdtDerivProdTyp>> IS NOT NULL"],
            "joiningConditions": [],
            "columnLevelConditions": "MAX (<<dm1.root->MTMRpt>>)"
        })
    },
    {
        "parent_path": "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_TRADE_MTM_NV/root.MTMRpt",
        "parent_objType": "DataSource",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_TRADE_CCR9_EXT_DERV_TYPE_JOIN/root.MTMRpt",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": [
                "AND <<tr_FLOW_TRADE_MTM_NV.QtrMonth>>=3 and <<tr_FLOW_TRADE_MTM_NV.SACCRAstCat>>='CDS' and <<tr_FLOW_TRADE_MTM_NV.CPC1ntTrdsFlg>> <> 0"
            ],
            "joiningConditions": [],
            "columnLevelConditions": []
        })
    },
    {
        "parent_path": None,  # root datasource
        "parent_objType": None,
        "child_path":  "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_TRADE_MTM_NV/root.MTMRpt",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["MTMRpt"]
        })
    },

    # ── PrchRecFlg — fan-in from two datasources ──────────────────────────────
    {
        "parent_path": None,
        "parent_objType": None,
        "child_path":  "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_CR_SEC/root.PrchRecFlg",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["PrchRecFlg"]
        })
    },
    {
        "parent_path": "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_CR_SEC/root.PrchRecFlg",
        "parent_objType": "DataSource",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_FLOW_AXIS_PRGMNAME_INT_JOIN/root.PrchRecFlg",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<tr_FLOW_AXIS_CR_SEC.AxiomRejectionReason>> = 'REPORTABLE'"],
            "joiningConditions": ["<<tr_FLOW_AXIS_CR_SEC.SecId>> = <<dmm_FLOW_AXIS_PRGMNAME_INT_JOIN.SecId>>"],
            "columnLevelConditions": ["<<dm1.root->PrchRecFlg>>"]
        })
    },
    {
        "parent_path": None,
        "parent_objType": None,
        "child_path":  "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_BOND_REF/root.PurchaseFlag",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["PurchaseFlag"]
        })
    },
    {
        "parent_path": "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_BOND_REF/root.PurchaseFlag",
        "parent_objType": "DataSource",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_FLOW_AXIS_PRGMNAME_INT_JOIN/root.PrchRecFlg",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<tr_FLOW_AXIS_BOND_REF.AssetClass>> = 'BOND'"],
            "joiningConditions": ["<<tr_FLOW_AXIS_BOND_REF.ISIN>> = <<dmm_FLOW_AXIS_PRGMNAME_INT_JOIN.ISIN>>"],
            "columnLevelConditions": ["COALESCE(<<dm2.root->PurchaseFlag>>, 0)"]
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_FLOW_AXIS_PRGMNAME_INT_JOIN/root.PrchRecFlg",
        "parent_objType": "ModifyModel",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_FLOW_AXIS_SEC_C_13_01_REDUCTION/Aggregation.PrchRecFlg",
        "child_objType": "Aggregation",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["MAX(<<dm1.root->PrchRecFlg>>)"]
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_FLOW_AXIS_SEC_C_13_01_REDUCTION/Aggregation.PrchRecFlg",
        "parent_objType": "Aggregation",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_SEC_C13_01_MAX_SUM/Aggregation.PrchRecFlg",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": []
        })
    },

    # ── SecId — single chain ──────────────────────────────────────────────────
    {
        "parent_path": None,
        "parent_objType": None,
        "child_path":  "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_CR_SEC/root.SecId",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["SecId"]
        })
    },
    {
        "parent_path": "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_CR_SEC/root.SecId",
        "parent_objType": "DataSource",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_FLOW_AXIS_PRGMNAME_INT_JOIN/root.SecId",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<tr_FLOW_AXIS_CR_SEC.AxiomRejectionReason>> = 'REPORTABLE'"],
            "joiningConditions": ["<<tr_FLOW_AXIS_CR_SEC.SecId>> = <<dmm_PRGMNAME.SecId>>"],
            "columnLevelConditions": []
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_FLOW_AXIS_PRGMNAME_INT_JOIN/root.SecId",
        "parent_objType": "ModifyModel",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_FLOW_AXIS_SEC_C_13_01_REDUCTION/Aggregation.SecId",
        "child_objType": "Aggregation",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": []
        })
    },
    {
        "parent_path": "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/Aggregation/agg_FLOW_AXIS_SEC_C_13_01_REDUCTION/Aggregation.SecId",
        "parent_objType": "Aggregation",
        "child_path":  "pr_DATA_ENRICHMENT_CRR3/1_0_0_0/ModifyModel/dmm_SEC_C13_01_MAX_SUM/Aggregation.SecId",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": []
        })
    },

    # ── pr_DATA_CRR3 / PrchRecFlg (single-hop lineage) ────────────────────────
    {
        "parent_path": None,
        "parent_objType": None,
        "child_path":  "pr_DATA_CRR3/1_0_0_0/DataSource/tr_FLOW_AXIS_CR_SEC/root.PrchRecFlg",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["PrchRecFlg"]
        })
    },

    # ── FINREP / GrossCarryAmt ────────────────────────────────────────────────
    {
        "parent_path": None,
        "parent_objType": None,
        "child_path":  "pr_DATA_FINREP/2_1_0/DataSource/tr_FINREP_LOAN_BOOK/root.CarryingAmount",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["CarryingAmount"]
        })
    },
    {
        "parent_path": "pr_DATA_FINREP/2_1_0/DataSource/tr_FINREP_LOAN_BOOK/root.CarryingAmount",
        "parent_objType": "DataSource",
        "child_path":  "pr_DATA_ENRICHMENT_FINREP/2_1_0/ModifyModel/dmm_FINREP_F01/Aggregation.GrossCarryAmt",
        "child_objType": "ModifyModel",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<tr_FINREP_LOAN_BOOK.AccountingStatus>> = 'PERFORMING'"],
            "joiningConditions": [],
            "columnLevelConditions": ["SUM(<<dm1.root->CarryingAmount>>)"]
        })
    },

    # ── COREP / CET1_Capital ──────────────────────────────────────────────────
    {
        "parent_path": None,
        "parent_objType": None,
        "child_path":  "pr_DATA_COREP/3_0_0/DataSource/tr_COREP_CAPITAL_RAW/root.Tier1Cap",
        "child_objType": "DataSource",
        "conditions": json.dumps({
            "rowLevelConditions": [],
            "joiningConditions": [],
            "columnLevelConditions": ["Tier1Cap"]
        })
    },
    {
        "parent_path": "pr_DATA_COREP/3_0_0/DataSource/tr_COREP_CAPITAL_RAW/root.Tier1Cap",
        "parent_objType": "DataSource",
        "child_path":  "pr_DATA_COREP_OWNFUNDS/3_0_0/Aggregation/agg_OWNFUNDS_TOTAL/Aggregation.CET1_Capital",
        "child_objType": "Aggregation",
        "conditions": json.dumps({
            "rowLevelConditions": ["<<tr_COREP_CAPITAL_RAW.CapitalTier>> = 'CET1'"],
            "joiningConditions": [],
            "columnLevelConditions": ["SUM(<<dm1.root->Tier1Cap>>)"]
        })
    },
]

_DUMMY_DATASOURCE_FIELDS = {
    "tr_flow_trade_mtm_nv": [
        {"datasource": "tr_flow_trade_mtm_nv", "field_name": "MTMRpt",        "description": "Mark to market report value", "data_type": "NUMBER",  "size": "18,4", "allow_nulls": "Y"},
        {"datasource": "tr_flow_trade_mtm_nv", "field_name": "QtrMonth",       "description": "Quarter month indicator",      "data_type": "NUMBER",  "size": "2",    "allow_nulls": "N"},
        {"datasource": "tr_flow_trade_mtm_nv", "field_name": "SACCRAstCat",    "description": "SA-CCR Asset category",        "data_type": "VARCHAR2","size": "10",   "allow_nulls": "Y"},
        {"datasource": "tr_flow_trade_mtm_nv", "field_name": "CPC1ntTrdsFlg",  "description": "Counterparty net trades flag",  "data_type": "NUMBER",  "size": "1",    "allow_nulls": "N"},
        {"datasource": "tr_flow_trade_mtm_nv", "field_name": "TradeId",         "description": "Trade identifier",             "data_type": "VARCHAR2","size": "50",   "allow_nulls": "N"},
        {"datasource": "tr_flow_trade_mtm_nv", "field_name": "Notional",        "description": "Notional amount",              "data_type": "NUMBER",  "size": "18,2", "allow_nulls": "Y"},
    ],
    "tr_flow_axis_cr_sec": [
        {"datasource": "tr_flow_axis_cr_sec", "field_name": "PrchRecFlg",          "description": "Purchase record flag",          "data_type": "NUMBER",  "size": "1",    "allow_nulls": "Y"},
        {"datasource": "tr_flow_axis_cr_sec", "field_name": "AxiomRejectionReason","description": "Axiom rejection reason code",   "data_type": "VARCHAR2","size": "50",   "allow_nulls": "Y"},
        {"datasource": "tr_flow_axis_cr_sec", "field_name": "SecId",               "description": "Security identifier",           "data_type": "VARCHAR2","size": "20",   "allow_nulls": "N"},
        {"datasource": "tr_flow_axis_cr_sec", "field_name": "FlowAmt",             "description": "Flow amount",                   "data_type": "NUMBER",  "size": "18,4", "allow_nulls": "Y"},
    ],
    "tr_flow_axis_bond_ref": [
        {"datasource": "tr_flow_axis_bond_ref", "field_name": "PurchaseFlag", "description": "Purchase flag",   "data_type": "NUMBER",  "size": "1",  "allow_nulls": "Y"},
        {"datasource": "tr_flow_axis_bond_ref", "field_name": "ISIN",         "description": "ISIN code",        "data_type": "VARCHAR2","size": "12", "allow_nulls": "N"},
        {"datasource": "tr_flow_axis_bond_ref", "field_name": "AssetClass",   "description": "Asset class code", "data_type": "VARCHAR2","size": "20", "allow_nulls": "Y"},
        {"datasource": "tr_flow_axis_bond_ref", "field_name": "Maturity",     "description": "Maturity date",    "data_type": "DATE",    "size": None, "allow_nulls": "Y"},
    ],
    "tr_finrep_loan_book": [
        {"datasource":"tr_finrep_loan_book","field_name":"CarryingAmount",   "description":"Loan carrying amount",   "data_type":"NUMBER",  "size":"18,2","allow_nulls":"Y"},
        {"datasource":"tr_finrep_loan_book","field_name":"AccountingStatus", "description":"PERFORMING or NPL",      "data_type":"VARCHAR2","size":"20",  "allow_nulls":"N"},
        {"datasource":"tr_finrep_loan_book","field_name":"LoanId",           "description":"Loan identifier",        "data_type":"VARCHAR2","size":"30",  "allow_nulls":"N"},
    ],
    "tr_corep_capital_raw": [
        {"datasource":"tr_corep_capital_raw","field_name":"Tier1Cap",    "description":"Tier 1 capital amount",  "data_type":"NUMBER",  "size":"18,2","allow_nulls":"Y"},
        {"datasource":"tr_corep_capital_raw","field_name":"CapitalTier", "description":"CET1 / AT1 / T2",        "data_type":"VARCHAR2","size":"10",  "allow_nulls":"N"},
        {"datasource":"tr_corep_capital_raw","field_name":"InstrumentId","description":"Instrument identifier",  "data_type":"VARCHAR2","size":"30",  "allow_nulls":"N"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# FETCH LAYER
# ─────────────────────────────────────────────────────────────────────────────

def fetch_applications() -> list[str]:
    if USE_DUMMY_DATA:
        return _DUMMY_APPLICATIONS
    return db_get_applications()


def fetch_datamodels(application: str) -> list[dict]:
    if USE_DUMMY_DATA:
        return _DUMMY_DATAMODELS.get(application, [])
    return db_get_datamodels(application)


def fetch_fields(application: str, model_name: str) -> list[dict]:
    if USE_DUMMY_DATA:
        return _DUMMY_FIELDS.get((application, model_name), [])
    return db_get_fields(application, model_name)


def fetch_all_edges(application: str, start_path: str) -> list[dict]:
    if USE_DUMMY_DATA:
        return _walk_dummy_edges(start_path)
    return db_get_all_edges_for_field(application, start_path)


def fetch_datasource_fields(application: str, datasource: str) -> list[dict]:
    if USE_DUMMY_DATA:
        return _DUMMY_DATASOURCE_FIELDS.get(datasource.lower(), [])
    return db_get_datasource_fields(application, datasource)


def fetch_datasources(application: str) -> list[str]:
    if USE_DUMMY_DATA:
        return sorted(_DUMMY_DATASOURCE_FIELDS.keys())
    return db_get_all_datasources(application)


def _walk_dummy_edges(start_path: str) -> list[dict]:
    """BFS upward through dummy edges. Returns all contributing edges."""
    # Index: child_path → list of edges
    child_idx: dict[str, list[dict]] = {}
    for e in _DUMMY_EDGES:
        cp = e.get("child_path")
        if cp:
            child_idx.setdefault(cp, []).append(e)

    visited_paths: set[str] = {start_path}
    visited_edge_keys: set[tuple] = set()
    result: list[dict] = []
    queue: list[str] = [start_path]

    while queue:
        current = queue.pop(0)
        for edge in child_idx.get(current, []):
            key = (edge.get("parent_path"), edge.get("child_path"))
            if key in visited_edge_keys:
                continue
            visited_edge_keys.add(key)
            result.append(edge)
            parent = edge.get("parent_path")
            if parent and parent not in visited_paths:
                visited_paths.add(parent)
                queue.append(parent)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PATH PARSING + NODE KEY (spec §3.1)
# ─────────────────────────────────────────────────────────────────────────────

def node_key(path: Optional[str]) -> Optional[str]:
    """Strip last /segment to collapse field-level paths to object-level nodes."""
    if not path:
        return None
    return path.rsplit("/", 1)[0] if "/" in path else path


def parse_node_key(nk: str) -> dict:
    """Parse a collapsed node key for display metadata."""
    if not nk:
        return {"short_label": "ROOT", "obj_type": "DataSource", "datasource": "ROOT"}
    parts = nk.split("/")
    obj_type = "Unknown"
    for t in ["DataSource", "ModifyModel", "Aggregation"]:
        if t in parts:
            obj_type = t
            break
    # last segment = object name (e.g. dmm_CCR9_REPORTING_INPUTS)
    obj_name = parts[-1]
    return {
        "short_label": obj_name,
        "obj_type":    obj_type,
        "datasource":  obj_name,   # for DataSource nodes this is the DS name
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONDITION NORMALISATION
# ─────────────────────────────────────────────────────────────────────────────

def _norm_list(val) -> list[str]:
    """Normalise rowLevelConditions / joiningConditions / columnLevelConditions."""
    if val is None or val == "" or val == []:
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if v and str(v).strip()]
    if isinstance(val, str):
        s = val.strip()
        return [s] if s else []
    return [str(val)]


def _safe_json(s) -> dict:
    if not s:
        return {}
    if isinstance(s, dict):
        return s
    try:
        return json.loads(s)
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH BUILDER  (spec §3–§4)
# ─────────────────────────────────────────────────────────────────────────────

def build_graph(edges: list[dict], start_path: Optional[str] = None) -> dict:
    """
    Implements spec §3–§4:
    - NodeKey collapse (§3.1)
    - Edge direction: ChildNode → ParentNode (§3.2)
    - Root = start_path (§3.3)
    - Leaf = parent_path is null (§3.4)
    - Deduplicate nodes and edges (§3.5)
    - col_expr on node (§4.1/§4.2.1)
    - row/join on edge (§4.1/§4.2.2)
    - Modal data: full conditions attached to each node for expand button
    """

    # ── Step 1: build node_key-level structures ──────────────────────────────

    # node_col_expr[nk]   = deduplicated list of col conditions
    # edge_row[src,tgt]   = deduplicated row conditions
    # edge_join[src,tgt]  = deduplicated join conditions
    # node_meta[nk]       = {obj_type, datasource, raw_paths}
    # leaf_set            = nk where parent_path is None
    # all_child_nks       = every child node key seen
    # all_parent_nks      = every parent node key seen (non-null)

    node_col_expr:  dict[str, list[str]] = {}
    edge_row:       dict[tuple, list[str]] = {}
    edge_join:      dict[tuple, list[str]] = {}
    node_meta:      dict[str, dict] = {}
    leaf_set:       set[str] = set()
    all_child_nks:  set[str] = set()
    all_parent_nks: set[str] = set()

    # Also store node-level modal data: incoming edges with full conditions
    # node_modal[nk] = list of condition dicts (one per incoming raw edge)
    node_modal: dict[str, list[dict]] = {}

    for e in edges:
        raw_parent = e.get("parent_path")
        raw_child  = e.get("child_path")
        if not raw_child:
            continue

        cond = _safe_json(e.get("conditions") or e.get("current_conditions"))

        col  = _norm_list(cond.get("columnLevelConditions"))
        rows = _norm_list(cond.get("rowLevelConditions"))
        jns  = _norm_list(cond.get("joiningConditions"))

        child_nk = node_key(raw_child)
        if not child_nk:
            continue

        # Register child node
        all_child_nks.add(child_nk)
        if child_nk not in node_meta:
            node_meta[child_nk] = parse_node_key(child_nk)
            node_meta[child_nk]["raw_path"] = raw_child

        # Accumulate col_expr onto child node (§4.2.1)
        if col:
            existing = node_col_expr.get(child_nk, [])
            for c in col:
                if c not in existing:
                    existing.append(c)
            node_col_expr[child_nk] = existing

        # Modal data per node
        if rows or jns or col:
            node_modal.setdefault(child_nk, []).append({
                "raw_child":  raw_child,
                "raw_parent": raw_parent,
                "col":  col,
                "rows": rows,
                "joins": jns,
            })

        if raw_parent is None:
            # Leaf/source
            leaf_set.add(child_nk)
            continue

        parent_nk = node_key(raw_parent)
        if not parent_nk:
            continue

        # Register parent node
        all_parent_nks.add(parent_nk)
        if parent_nk not in node_meta:
            node_meta[parent_nk] = parse_node_key(parent_nk)
            node_meta[parent_nk]["raw_path"] = raw_parent

        # Accumulate edge row/join (§4.2.2)
        ek = (child_nk, parent_nk)
        for r in rows:
            lst = edge_row.setdefault(ek, [])
            if r not in lst:
                lst.append(r)
        for j in jns:
            lst = edge_join.setdefault(ek, [])
            if j not in lst:
                lst.append(j)

    # ── Step 2: find root (spec §3.3) ────────────────────────────────────────

    if start_path:
        start_nk = node_key(start_path)
    else:
        # Sink = child_nks not in parent_nks
        sinks = sorted(all_child_nks - all_parent_nks)
        start_nk = sinks[0] if sinks else None

    # ── Step 3: assemble output ───────────────────────────────────────────────

    all_nks = set(node_meta.keys())

    nodes_out = []
    for nk, meta in node_meta.items():
        is_leaf = nk in leaf_set
        obj_type = meta["obj_type"]
        if is_leaf:
            obj_type = "DataSource"

        # Attach full modal conditions for expand button
        modal_conds = node_modal.get(nk, [])

        nodes_out.append({
            "id":         nk,
            "label":      meta["short_label"],
            "datasource": meta["datasource"],
            "obj_type":   obj_type,
            "path":       nk,
            "col_expr":   node_col_expr.get(nk, []),
            "is_leaf":    is_leaf,
            "is_root":    nk == start_nk,
            # Full condition detail for modal
            "modal": {
                "col":   node_col_expr.get(nk, []),
                "incoming": modal_conds,
            }
        })

    edges_out = []
    seen_edges: set[tuple] = set()
    for (child_nk, parent_nk), _ in {**{k: None for k in edge_row}, **{k: None for k in edge_join}}.items():
        if (child_nk, parent_nk) in seen_edges:
            continue
        seen_edges.add((child_nk, parent_nk))
        labels = []
        for r in edge_row.get((child_nk, parent_nk), []):
            labels.append({"type": "row",  "text": r})
        for j in edge_join.get((child_nk, parent_nk), []):
            labels.append({"type": "join", "text": j})
        edges_out.append({"source": child_nk, "target": parent_nk, "labels": labels})

    # Also add edges with no labels (pure flow edges)
    for e in edges:
        raw_parent = e.get("parent_path")
        raw_child  = e.get("child_path")
        if not raw_child or raw_parent is None:
            continue
        child_nk  = node_key(raw_child)
        parent_nk = node_key(raw_parent)
        if not child_nk or not parent_nk:
            continue
        ek = (child_nk, parent_nk)
        if ek in seen_edges:
            continue
        seen_edges.add(ek)
        edges_out.append({"source": child_nk, "target": parent_nk, "labels": []})

    # Datasources = leaf node datasource names
    datasources = sorted({
        n["datasource"]
        for n in nodes_out
        if n["obj_type"] == "DataSource" and n["datasource"]
    })

    return {
        "nodes":       nodes_out,
        "edges":       edges_out,
        "datasources": datasources,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Data Lineage API v2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/applications")
def get_applications():
    return {"applications": fetch_applications()}


@app.get("/api/datamodels")
def get_datamodels(application: str):
    if not application:
        raise HTTPException(400, "application required")
    return {"application": application, "datamodels": fetch_datamodels(application)}


@app.get("/api/datamodels/{model_name}/fields")
def get_fields(model_name: str, application: str):
    if not application:
        raise HTTPException(400, "application required")
    fields = fetch_fields(application, model_name)
    if not fields:
        raise HTTPException(404, f"Model '{model_name}' not found")
    return {"application": application, "model_name": model_name, "fields": fields}


@app.get("/api/lineage")
def get_lineage(application: str, field_path: str):
    if not application:
        raise HTTPException(400, "application required")
    edges = fetch_all_edges(application, field_path)
    if not edges:
        raise HTTPException(404, f"No lineage for: {field_path}")
    return build_graph(edges, start_path=field_path)


@app.get("/api/datasource/{name}/fields")
def get_datasource_fields_endpoint(name: str, application: str):
    fields = fetch_datasource_fields(application, name)
    if not fields:
        raise HTTPException(404, f"No fields for datasource '{name}'")
    return {"application": application, "datasource": name, "fields": fields}


@app.get("/")
def serve_index():
    return FileResponse("indexv2.html")


app.mount("/static", StaticFiles(directory="static"), name="static")