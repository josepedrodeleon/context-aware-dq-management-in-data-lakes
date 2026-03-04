import pandas as pd
import uuid
import datetime
from metadata import metadata_utils
from data_quality import metrics


def SanitizeMovies(input_path, output_path):
    # Read
    clean_merge = pd.read_csv(input_path)
    
    # Transform
    clean_merge["release_date"] = clean_merge["release_date"].fillna("1800-01-01")
    clean_merge["genres"] = clean_merge["genres"].fillna("Sin Datos")
    clean_merge["production_countries"] = clean_merge["production_countries"].fillna("Sin Datos")
    
    # Metadata
    db_id = uuid.uuid4()
    db_metadata = {
        "db_name": "DB - Movies_ML.csv",
        "db_id": db_id,
        "db_description": "Movies_ML Dataset",
        "ingestion_date": str(datetime.datetime.now()),
        "table_name": "Movies_ML.csv",
        "table_id": uuid.uuid4(),
        "table_description": "Table - Movies_ML Dataset",
        "zone": "refined-zone"
    }
    metadata_utils.save_database_metadata(db_metadata, clean_merge)
    
    process_metadata = {
        "id_process": uuid.uuid4(),
        "name": "tr:SanitizeMovies",
        "description": "Clean TMDB Dataset",
        "date": str(datetime.datetime.now()),
        "source_dataset_name": "DB - movie_ratings.csv",
        "target_id": db_id,
        "zone": "refined-zone"
    }
    metadata_utils.save_process_metadata(process_metadata)
    
    # DQ Step
    dq_step(db_id, clean_merge)
    
    # Save
    clean_merge.to_csv(output_path, index=False)

def dq_step(db_id, df):
    metadata_utils.link_context_dqm_data_metadata('dqm1', db_id)
    metric_dict = {
        "ame5": metrics.ratioNoNulos(df, "title"),
        "ame6": metrics.ratioNoNulos(df, "genres"),
        "ame7": metrics.ratioNoNulos(df, "release_date"),
        "ame8": metrics.ratioNoNulos(df, "vote_average"),
        "ame9": metrics.ratioNoNulos(df, "vote_count"),
        "ame10": metrics.ratioNoNulos(df, "production_countries"),
        "ame11": metrics.ratioNoNulosNiSD(df, "genres", ['Sin Datos', '1800-01-01', 0]),
        "ame12": metrics.ratioNoNulosNiSD(df, "release_date", ['Sin Datos', '1800-01-01', 0]),
        "ame13": metrics.ratioNoNulosNiSD(df, "vote_average", ['Sin Datos', '1800-01-01', 0]),
        "ame14": metrics.ratioNoNulosNiSD(df, "vote_count", ['Sin Datos', '1800-01-01', 0]),
        "ame15": metrics.ratioNoNulosNiSD(df, "production_countries", ['Sin Datos', '1800-01-01', 0])
    }
    metadata_utils.load_metric_metadata(metric_dict)


