import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def ratioNoNulos(dataset, column_name, valores_SD=None):
    if (valores_SD):
        return(ratioNoNulosNiSD(dataset, column_name, valores_SD))
    
    total_values = len(dataset)
    non_null_values = dataset[column_name].notnull().sum()
    return (non_null_values / total_values) * 100

def ratioNoNulosNiSD(dataset, column_name, valores_SD):
    filtered_values = dataset[column_name].notnull() & ~dataset[column_name].isin(valores_SD)
    total_values = len(dataset)
    valid_values = filtered_values.sum()
    return (valid_values / total_values) * 100