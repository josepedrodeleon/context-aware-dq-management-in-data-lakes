import pandas as pd
import numpy as np
import uuid
import datetime
from metadata import metadata_utils
from data_quality import metrics


def ingest_title_ratings_dataset(input_path, output_path):
    # Extract
    title_ratings_dataset = pd.read_csv(input_path)
    
    # Metadata preparation
    db_id = uuid.uuid4()
    db_metadata = {
        "db_name": "DB - title.ratings.tsv",
        "db_id": db_id,
        "db_description": "title.ratings.tsv",
        "ingestion_date": str(datetime.datetime.now()),
        "table_name": "title.ratings.tsv",
        "table_id": uuid.uuid4(),
        "table_description": "IMDB Title Ratings",
        "zone": "raw-zone"
    }
    metadata_utils.save_database_metadata(db_metadata, title_ratings_dataset)
    
    process_metadata = {
        "id_process": uuid.uuid4(),
        "name": "Ingest IMDB Title Ratings",
        "description": "Ingest IMDB Title Ratings",
        "date": str(datetime.datetime.now()),
        "target_id": db_id,
        "zone": "landing-zone"
    }
    metadata_utils.save_process_metadata(process_metadata)
    
    # DQ Step
    title_ratings_dq_step(title_ratings_dataset)
    
    # Save
    title_ratings_dataset.to_csv(output_path, index=False)
    
    
def title_ratings_dq_step(df):
    pass


def ingest_TMDB_dataset(input_path, output_path):
    # Extract
    TMDB_ratings_dataset = pd.read_csv(input_path)
    
    # Metadata preparation
    db_id = uuid.uuid4()
    db_metadata = {
        "db_name": "DB - TMDB_movie_dataset_v11.csv",
        "db_id": db_id,
        "db_description": "TMDB Movie Dataset",
        "ingestion_date": str(datetime.datetime.now()),
        "table_name": "TMDB_movie_dataset_v11.csv",
        "table_id": uuid.uuid4(),
        "table_description": "TMDB Movie Dataset",
        "zone": "raw-zone"
    }
    metadata_utils.save_database_metadata(db_metadata, TMDB_ratings_dataset)
    
    process_metadata = {
        "id_process": uuid.uuid4(),
        "name": "Ingest TMDB Movie Dataset",
        "description": "Ingest IMDB Title Ratings",
        "date": str(datetime.datetime.now()),
        "target_id": db_id,
        "zone": "landing-zone"
    }
    metadata_utils.save_process_metadata(process_metadata)
    
    # DQ Step
    TMDB_dq_step(db_id, TMDB_ratings_dataset)
    
    # Save
    TMDB_ratings_dataset.to_csv(output_path, index=False)


def TMDB_dq_step(db_id, df):
    metadata_utils.link_context_dqm_data_metadata('dqm3', db_id)
    metric_dict = {
        "ame39": metrics.ratioNoNulos(df, "title", []),
        "ame40": metrics.ratioNoNulos(df, "genres", []),
        "ame41": metrics.ratioNoNulos(df, "release_date", []),
        "ame42": metrics.ratioNoNulosNiSD(df, "vote_average", [0.0]),
        "ame43": metrics.ratioNoNulos(df, "vote_count", [0.0]),
        "ame44": metrics.ratioNoNulos(df, "production_countries", [])
    }
    metadata_utils.load_metric_metadata(metric_dict)