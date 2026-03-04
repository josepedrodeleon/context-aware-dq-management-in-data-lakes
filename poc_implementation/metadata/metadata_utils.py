import uuid
from neo4j import GraphDatabase
import pandas as pd
from neo4j import GraphDatabase
import os
import datetime

uri = "bolt://localhost:7687"
user = "neo4j"
password = "password"

def execute_query(query):
    #print("Executing Query: ", query)
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run(query)
    driver.close()
    return result


def create_zones(zones=["landing-zone", "raw-zone", "trusted-zone", "refined-zone"]):
    query_template = """
        MERGE({zone_variable}: Zone {{name: '{zone_name}'}})
    """
    
    query = ''
    for zone in zones:
        query += query_template.format(
            zone_name=zone,
            zone_variable=zone[0:2]
        )
    
    execute_query(query)

    
def save_database_metadata(params, df=None):
    query = f"""
        MERGE (dataset:Dataset:Database {{
            id_dataset: '{params["db_id"]}',
            name: '{params["db_name"]}', 
            description: '{params["db_description"]}', 
            ingestion_date: '{params["ingestion_date"]}'
        }})
        MERGE (table:Table {{
            id_table: '{params["table_id"]}',
            name: '{params["table_name"]}',
            description: '{params["table_description"]}'
        }})  WITH dataset, table
        MATCH (zone:Zone {{name: '{params["zone"]}'}})
        MERGE (dataset)-[:STORED_IN]->(zone)
        MERGE (table)-[:BELONGS_TO_DB]->(dataset)
    """
    
    execute_query(query)
    save_column_data(params, df)
    
    
def infer_column_type(series):
    if series.dtype.kind in {'i', 'u', 'f'}:
        return "numeric"
    elif series.dtype.kind in {'b'}:
        return "boolean"
    elif series.dtype.kind in {'M'}:
        return "datetime"
    else:
        return "string"


def save_column_data(params, df):
    table_id = params["table_id"]
    query = f"MATCH (table:Table {{id_table: '{table_id}'}})\n"
    for col in df.columns:
        column_id = str(uuid.uuid4())
        column_type = infer_column_type(df[col])
        query += f"""
        MERGE (col_{column_id.replace('-', '')}:Column {{
            id_column: '{column_id}',
            name: '{col}',
            column_type: '{column_type}'
        }})
        MERGE (col_{column_id.replace('-', '')})-[:BELONGS_TO_TABLE]->(table)
        """

    execute_query(query)


def save_process_metadata(params):
    query = f"""
        MERGE (process:Process {{
            id_process: '{params["id_process"]}',
            name: '{params["name"]}', 
            description: '{params["description"]}', 
            date: '{params["date"]}'
        }})
        WITH process
        MATCH (zone:Zone {{name: '{params["zone"]}'}})
        MATCH (target_dataset:Dataset {{id_dataset: '{params["target_id"]}'}})
        MERGE (process)-[:EXECUTED_IN]->(zone)
        WITH process, target_dataset
        MERGE (target_dataset)-[:IS_TARGET]->(process)
    """

    if "source_dataset_name" in params and params["source_dataset_name"]:
        query += f"""
        WITH process
        MATCH (source_dataset:Dataset {{name: '{params["source_dataset_name"]}'}})
        MERGE (process)-[:HAS_SOURCE]->(source_dataset)
        """

    if "source_2_dataset_name" in params and params["source_2_dataset_name"]:
        query += f"""
        WITH process
        MATCH (source_dataset_2:Dataset {{name: '{params["source_2_dataset_name"]}'}})
        MERGE (process)-[:HAS_SOURCE]->(source_dataset_2)
        """

    execute_query(query)


def link_context_dqm_data_metadata(dqm_id, dataset_id):
    ## Vincula metadatos de datos y procesos con los de calidad y contexto
    column_query = f"""
        MATCH (dqModel:DQModel {{id: '{dqm_id}'}})<-[:BELONGS_TO]-(method:AppliedDQMethod)
        MATCH (ctxm:ContextModel)-[:CONTEXTUALIZES_DQM]->(dqModel)
        MATCH (col:Column)-[:BELONGS_TO_TABLE]->(t:Table)-[:BELONGS_TO_DB]->(d:Database {{id_dataset: '{dataset_id}'}})
        WHERE method.appliedTo = col.name AND method.appliedTo <> ''
        MERGE (method)-[:APPLIED_TO]->(col)
        MERGE (dqModel)-[:MODELS_DQ_FOR]->(d)
        MERGE (ctxm)-[:CONTEXTUALIZES_DATASET]->(d);
    """
    
    dataset_query = f"""
        MATCH (dqModel:DQModel {{id: '{dqm_id}'}})<-[:BELONGS_TO]-(method:AppliedDQMethod {{appliedTo: ''}})
        MATCH (d:Database {{id_dataset: '{dataset_id}'}})
        MERGE (method)-[:APPLIED_TO]->(d);
    """
    execute_query(column_query)
    execute_query(dataset_query)


def load_metric_metadata(method_dict):
    query = ""
    for i, (method_id, measure_value) in enumerate(method_dict.items()):
        dq_id = str(uuid.uuid4())
        exec_date = str(datetime.datetime.now())
        query += (
            f"MATCH (m{i}:AppliedDQMethod {{id: '{method_id}'}}) "
            f"CREATE (dq{i}:DQMeasure {{"
            f"id: '{dq_id}', execution_date: '{exec_date}', measure_value: {measure_value}"
            f"}}) "
            f"MERGE (dq{i})-[:EXECUTES]->(m{i}) "
            f"WITH m{i}, dq{i} "
        )

    if query.endswith(" "):
        query = query.rstrip()
    if query.endswith(f"WITH m{i}, dq{i}"):
        query = query[: -len(f"WITH m{i}, dq{i}")]

    execute_query(query)