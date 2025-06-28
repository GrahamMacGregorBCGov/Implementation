# %%
import geopandas as gpd
import numpy as np

hexgdb = r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\Hexagon Grids\Hexagon_PU_2024_12_11.gdb'

brfn_gdb = r"\\spatialfiles.bcgov\work\srm\nr\NEGSS\NEDD\First_Nations_Agreements\BRFN_Implementation_Agreement\FileGeodatabase\BRFNAgreement.gdb"

outgdb = r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Deliverables\AFLB_ExportLayers\WMB_AFLB_gpd2.gdb'

trapgdf = gpd.read_file(brfn_gdb, layer='BRFN_Traplines_Numbered')
wmbgdf = gpd.read_file(brfn_gdb, layer='Priority_WMB')
hexgdf = gpd.read_file(hexgdb, layer='Hex_1ha_WMB_SA')
hexgdf.set_index("GRID_ID", inplace=True)
# AFLB (area forested land base)
aflbgdf = gpd.read_file(r"\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\AFLB_IFLB_StudyArea_2023-10-31_NorthRoss\AFLB_IFLB_StudyArea_2024-12-04_NorthRoss.shp")

owngdf = gpd.read_file(r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\ownership\iflb_own_studyArea.shp')

#%%
# split aflb along grid for preformance in selection

def split_grid(polygon, edge_size):
    """_summary_

    Args:
        polygon (shapely.geometry): input poly to split
        edge_size (numeric): distance to create grid out of

    Returns:
        geopandas.GeoDataFrame: output geodataframe split into squares of length edge_size
    """
    from itertools import product
    import numpy as np
    import geopandas as gpd
    
    # make grid
    bounds = polygon.bounds
    x_coords = np.arange(bounds[0] + edge_size/2, bounds[2], edge_size)
    y_coords = np.arange(bounds[1] + edge_size/2, bounds[3], edge_size)
    combinations = np.array(list(product(x_coords, y_coords)))
    squares = gpd.points_from_xy(combinations[:, 0], combinations[:, 1]).buffer(edge_size / 2, cap_style=3)

    # Intersect with grid
    intersection = squares.intersection(polygon)
    # remove empty geom
    intersection = intersection[~intersection.is_empty]
    # GeometryArray to GeoDataFrame
    intersection_gdf = gpd.GeoDataFrame(crs = 3005, geometry=intersection)
    return intersection_gdf
# %%
def intersectPolys(df1, df2):
    import pandas as pd
    gdf_out = gpd.GeoDataFrame()
    df1_sindex = df1.sindex
    
    for poly in df2.geometry:
        type(poly)
        # # find approximate matches with r-tree, then precise matches from those approximate ones
        possible_matches_index = list(df1_sindex.intersection(poly.bounds))
        possible_matches = df1.iloc[possible_matches_index]
        precise_matches = possible_matches[possible_matches.intersects(poly)]
        precise_matches = possible_matches
        # remove duplicates (cells overlapping two grids) before merging
        precise_matches = precise_matches[~precise_matches.index.isin(gdf_out.index)]
        gdf_out = pd.concat([gdf_out, precise_matches])
    return gdf_out

#%%
aflb_geom = aflbgdf.loc[aflbgdf['OWN_AFLB'] == 'AFLB'].iloc[0].geometry
if not aflb_geom.isvalid:
    from shapely.validation import make_valid
    aflb_geom = make_valid(aflb_geom)
    
del aflbgdf
aflb_grid_gdf = split_grid(aflb_geom, 1000) # 100 ha grid rectangles
aflb_grid_gdf.to_file(r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\AFLB_IFLB_StudyArea_2023-10-31_NorthRoss\AFLB_grid\AFLB_grid_2.gpkg')
#%%
# aflb_grid_gdf = gpd.read_file(r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\AFLB_IFLB_StudyArea_2023-10-31_NorthRoss\AFLB_grid\AFLB_grid_2.gpkg', layer='AFLB_grid_2')
#%%
# First select and export the AFLB hexes in the WMB
import time
t0 = time.time()

# dictionary of requested trapline numbers by WMB for report
traplineDict = {
    'Upper Beatton River': ['TR0745T004', 'TR0745T003', 'TR0746T003'],
    'Blueberry River': ['TR0745T002', 'TR0745T003', 'TR0745T007'],
    'Middle Beatton River': ['TR0746T003', 'TR0745T003', 'TR0745T007'],
    'Lower Sikanni Chief River': ['TR0747T002', 'TR0747T004', 'TR0747T006']
    }

for wmb in traplineDict.keys():
    t1 = time.time()
    print(t1-t0)
    
    # Get hexes in WMB
    wmb_geom = wmbgdf.loc[wmbgdf['WATER_MANAGEMENT_BASIN_NAME'] == wmb].iloc[0].geometry
    wmb_hex_gdf = hexgdf.iloc[hexgdf.sindex.query(wmb_geom, predicate="intersects")]
    
    # Get WMB hex indices intersecting AFLB
    aflb_wmb_hex = wmb_hex_gdf.sindex.query(aflb_grid_gdf.geometry, predicate="intersects")[1] # the [1] selects the hex int indices (not the AFLB index)
    # filter to unique hexes
    aflb_wmb_hex = np.unique(aflb_wmb_hex)
    
    # Get WMB hex indices intersecting excluded land ownership classes
    excluded_wmb_hex = wmb_hex_gdf.sindex.query(owngdf.geometry, predicate="intersects")[1]
    excluded_wmb_hex = np.unique(excluded_wmb_hex)
    
    # remove excluded hexes from AFLB
    final_aflb_wmb_hex = [x for x in aflb_wmb_hex if x not in excluded_wmb_hex]
    
    # create gdf and export
    aflb_wmb_hex_gdf = wmb_hex_gdf.iloc[final_aflb_wmb_hex]
    aflb_wmb_hex_gdf.to_file(outgdb, layer=f"AFLB_hex_{wmb}", driver='OpenFileGDB')
    
    t2 = time.time()
    print(t2-t1)
    
    # select subset by trapline
    for trapline in traplineDict[wmb]:
        trapline_geom = trapgdf.loc[trapgdf["TRAPLINE_AREA_IDENTIFIER"] == trapline].iloc[0].geometry
        
        # select cells intersecting trapline and export
        trap_wmb_hex_gdf = aflb_wmb_hex_gdf.iloc[aflb_wmb_hex_gdf.sindex.query(trapline_geom, predicate="intersects")]
        
        if len(trap_wmb_hex_gdf) == 0:
            print(f"NOTHING IN {wmb} AND {trapline}")
        else:
            trap_wmb_hex_gdf.to_file(outgdb, layer=f"AFLB_hex_{wmb}_{trapline}", driver='OpenFileGDB')

# %%
# Next do HV1s and crown land
# Read HV1s and Crown Land
hv1_gdf = gpd.read_file(brfn_gdb, layer='BRFN_HV1')
# crwn_gdf = gpd.read_file(r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\ownership\crown_studyarea.gpkg', layer = 'Crown_Hv1C')
crwn_gdf = gpd.read_file(r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Data\ownership\crown_studyarea.gpkg', layer = 'Crown_studyarea')

#%%
def getCrownHexes(geom):
    """Returns a gdf of all hexagons on crown land and in the input geometry

    Args:
        geom (shapely.Geometry): Polygon or MultiPolygon of the area to search for crown land hexagons in.

    Returns:
        geopandas.GeoDataFrame: GeoDataFrame of hexagons intersecting both crown land and the input geom.
    """
    # get hex ids in geometry:
    geom_hex = hexgdf.sindex.query(geom, predicate="intersects")
    
    # get gdf from hexes
    geom_hex_gdf = hexgdf.iloc[geom_hex]
    
    # Refine hex gdf to crown land
    plan_crown_hex = geom_hex_gdf.sindex.query(crwn_gdf.geometry, predicate="intersects")
    
    # refine to only unique values from the hexes (second array).
    # this is because the sindex.query() returns two arrays representing ids from both geometry sets
    # we only want the ids for the hexes, and we don't care how many crown land polys they overlap.
    plan_crown_hex = np.unique(plan_crown_hex[1])
    
    # return as gdf of hexes
    return geom_hex_gdf.iloc[plan_crown_hex]
    
    
#%%
# export files for hexes in Grizzly Creek and Upper Halfway HV1C plans
for plan in ['Grizzly Creek', 'Upper Halfway']:
    # Get union geom of HV1 polys
    plan_geom = hv1_gdf.loc[hv1_gdf['PlanName'] == plan].geometry.unary_union
    
    plan_crown_hex_gdf = getCrownHexes(plan_geom)
    plan_crown_hex_gdf.to_file(outgdb, layer=f"Crown_hex_HV1C_{plan}", driver='OpenFileGDB')
# %%
# export files for the three HV1 zones (one for A, B, C)
for zone in ['A', 'B', 'C']:
    zone_geom = hv1_gdf.loc[hv1_gdf['Zone_A_B_C'] == zone].geometry.unary_union
    
    zone_crown_hex_gdf = getCrownHexes(zone_geom)
    zone_crown_hex_gdf.to_file(outgdb, layer=f"Crown_hex_HV1{zone}", driver='OpenFileGDB')

# %%
from fiona import listlayers
import geopandas as gpd

gdb = r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Deliverables\AFLB_ExportLayers\AreaBasedFatures_2025-01-10.gdb'

df = gpd.read_file(gdb, layer = 'PU50ha_UpperBeattonRiver_2025_01_10')

# %%
listlayers(r'\\spatialfiles.bcgov\work\srm\fsj\Workarea\nross\WMBPlanning\Deliverables\HexagonOutputs\ContiguousHabitatHex_2024_12_19.gdb')