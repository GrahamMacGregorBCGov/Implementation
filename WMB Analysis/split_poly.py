def split_grid(polygon, edge_size):
    """_summary_

    Args:
        polygon (shapely.geometry): input poly to split
        edge_size (numeric): distance to create grid out of

    Returns:
        geopandas.GeoDataFrame: _description_
    """
    from itertools import product
    import numpy as np
    import geopandas as gpd
    
    bounds = polygon.bounds
    x_coords = np.arange(bounds[0] + edge_size/2, bounds[2], edge_size)
    y_coords = np.arange(bounds[1] + edge_size/2, bounds[3], edge_size)
    combinations = np.array(list(product(x_coords, y_coords)))
    squares = gpd.points_from_xy(combinations[:, 0], combinations[:, 1]).buffer(edge_size / 2, cap_style=3)

    intersection = gpd.overlay(df1=polygon, df2=squares, how="intersection", keep_geom_type=True)
    return intersection
    