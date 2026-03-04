import pandas as pd
import uuid
import datetime
from metadata import metadata_utils
from data_quality import metrics


def CleanTMDB(raw_dataset_path, output_path):
    # Read dataset
    tmdb_Dataset = pd.read_csv(raw_dataset_path)
    
    # Execute transformation
    tmdb_Dataset = tmdb_Dataset.sort_values(by='id', ascending=True).reset_index(drop=True)
    Movies_Clean = tmdb_Dataset[['id','title','imdb_id', 'genres', 'status', 'adult','release_date','runtime','vote_average','vote_count','revenue','budget', 'popularity', 'original_language' , 'production_countries']]
    Movies_Clean = Movies_Clean.dropna(subset=["imdb_id"])
    Movies_Clean = Movies_Clean.drop_duplicates()
    
    # Metadata
    db_id = uuid.uuid4()
    db_metadata = {
        "db_name": "DB - TMDB_movies_clean.csv",
        "db_id": db_id,
        "db_description": "TMDB Movie Clean Dataset",
        "ingestion_date": str(datetime.datetime.now()),
        "table_name": "TMDB_movies_clean.csv",
        "table_id": uuid.uuid4(),
        "table_description": "Table - TMDB Movie Clean Dataset",
        "zone": "trusted-zone"
    }
    metadata_utils.save_database_metadata(db_metadata, tmdb_Dataset)
    
    process_metadata = {
        "id_process": uuid.uuid4(),
        "name": "tr:CleanTMDB",
        "description": "Clean TMDB Dataset",
        "date": str(datetime.datetime.now()),
        "source_dataset_name": "DB - TMDB_movie_dataset_v11.csv",
        "target_id": db_id,
        "zone": "trusted-zone"
    }
    metadata_utils.save_process_metadata(process_metadata)
    
    # DQ Step
    
    # Save
    Movies_Clean.to_csv(output_path, index=False)


def MergeTMDBandRatings(input_path_1, input_path_2, output_path):
    # Read
    TMDB_movies_clean_dataset = pd.read_csv(input_path_1)
    
    # Transform
    title_ratings_dataset = pd.read_csv(input_path_2, sep='\t')
    output = pd.merge(TMDB_movies_clean_dataset, title_ratings_dataset, left_on="imdb_id", right_on="tconst", how="left")
    output = output.drop(columns=["vote_average","vote_count"]).rename(columns={"averageRating": "vote_average","numVotes":"vote_count"})
    
    
    # Metadata
    db_id = uuid.uuid4()
    db_metadata = {
        "db_name": "DB - movie_ratings.csv",
        "db_id": db_id,
        "db_description": "Merged movie ratings Dataset",
        "ingestion_date": str(datetime.datetime.now()),
        "table_name": "movie_ratings.csv",
        "table_id": uuid.uuid4(),
        "table_description": "Table - Merged movie ratings Dataset",
        "zone": "trusted-zone"
    }
    metadata_utils.save_database_metadata(db_metadata, output)
    
    process_metadata = {
        "id_process": uuid.uuid4(),
        "name": "tr:MergeTMDBandRatings",
        "description": "Merge TMDB and Ratings",
        "date": str(datetime.datetime.now()),
        "source_dataset_name": "DB - TMDB_movies_clean.csv",
        "source_2_dataset_name": "DB - title.ratings.tsv",
        "target_id": db_id,
        "zone": "trusted-zone"
    }
    metadata_utils.save_process_metadata(process_metadata)
    
    dq_step(db_id, output)
    
    output.to_csv(output_path, index=False)

def dq_step(db_id, df):
    metadata_utils.link_context_dqm_data_metadata('dqm2', db_id)
    metric_dict = {
        "ame25": metrics.ratioNoNulos(df, "title"),
        "ame26": metrics.ratioNoNulos(df, "genres"),
        "ame27": metrics.ratioNoNulos(df, "release_date"),
        "ame28": metrics.ratioNoNulos(df, "vote_average"),
        "ame29": metrics.ratioNoNulos(df, "vote_count"),
        "ame30": metrics.ratioNoNulos(df, "production_countries")
    }
    metadata_utils.load_metric_metadata(metric_dict)

