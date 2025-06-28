#%%
# Import libraries
import sys
import duckdb
import fiona
import os
from shapely import clip_by_rect
from shapely.geometry import shape, MultiPolygon, Polygon, GeometryCollection
from time import time

sys.path.append("\\spatialfiles2.bcgov\work\FOR\RNI\DPC\General_User_Data\nross\BRFN_NE_LUPCE_Analysis\scripts\WMB_Analysis")
from bcgw2gdf import bcgw2gdf

bcgw2gdf = bcgw2gdf()


vri_url = "https://nrs.objectstore.gov.bc.ca/rczimv/geotest/veg_comp_layer_r1_poly.parquet"
aoi_path = r'\\spatialfiles.bcgov\work\srm\nr\NEGSS\NEDD\First_Nations_Agreements\BRFN_Implementation_Agreement\Shapefiles\CameronWMB.shp'
# aoi_path = r'\\spatialfiles2.bcgov\work\FOR\RNI\DPC\General_User_Data\nross\BRFN_NE_LUPCE_Analysis\WMB_Study_Area_2024_07_30\WMB_Study_Area_2024_07_30.shp'

workspace = r'C:\Users\nross\OneDrive - Government of BC\Documents\BRFNDocs\aflb-test'
outfile = os.path.join(workspace, 'shp', 'aflb.shp')

# Set the length of the squares that the AOI will be split into for processing and rejoin.
# Set to 0 to not split AOI
split_length = 10000

# Connect to Duckdb and load extensions
conn = duckdb.connect(os.path.join(workspace, 'aflb.db'))
conn.install_extension("httpfs")
conn.install_extension("spatial")
conn.load_extension("httpfs")
conn.load_extension("spatial")

#%%
# read AOI shapefile
with fiona.open(aoi_path) as shapefile:
    aoi = shape(shapefile[0]['geometry'])
    aoiBoundsStr = str(aoi.bounds)
    aoi_area_ha = aoi.area/10000
    print("AOI area ha: ", round(aoi_area_ha, 2))

# define Oracle SQL string for intersecting with the bounds of the AOI
intersectString = f"""
SDO_GEOMETRY(2003, 3005, NULL,
        SDO_ELEM_INFO_ARRAY(1,1003,3),
        SDO_ORDINATE_ARRAY{aoiBoundsStr} 
    )
"""
#%%
# split AOI into 50,000 x 50,000m squares (250,000 ha)
if split_length > 0:
    aoi_split_list = []
    ymax = xmax = count = 0
    while ymax <= aoi.bounds[3] and xmax <= aoi.bounds[2]:
        for ix in range(0, count+1):
            for iy in range(0, count+1):
                xmin = aoi.bounds[0] + (ix * split_length)
                ymin = aoi.bounds[1] + (iy * split_length)
                xmax = aoi.bounds[0] + ((1 + ix) * split_length)
                ymax = aoi.bounds[1] + ((1 + iy) * split_length)
                i_aoi = clip_by_rect(aoi, xmin, ymin, xmax, ymax)
                if i_aoi.area > 0 and i_aoi not in aoi_split_list:
                    aoi_split_list.append(i_aoi)
        count += 1

    print(f"Split AOI into {len(aoi_split_list)} squares of {split_length}m length ({(split_length**2)/10000} ha)")
else:
    aoi_split_list = [aoi]
    print("Did not split the AOI.")
#%%
def get_vri(aoi_split):
    # Create dissolved VRI table in Duckdb. Download VRI from Parquet object. 
    # See https://github.com/bcgov/gis-pantry/blob/0bb91df02b6c8fe00f4914679e3804ba71ea9020/recipes/duckdb/duckdb-geospatial.ipynb
    conn.sql(f"""
        CREATE OR REPLACE TEMP TABLE vri_temp as (
            SELECT ST_Union_Agg(Shape) as geom, SUM(POLYGON_AREA) as POLYGON_AREA, 
            FROM '{vri_url}' -- read parquet file from objectstorage
            WHERE 
                ST_Intersects (Shape, ST_GeomFromText('{aoi_split}'))
            AND
                BCLCS_LEVEL_1 != 'N' AND BCLCS_LEVEL_2 != 'W' AND BCLCS_LEVEL_3 != 'W'
            AND
                FOR_MGMT_LAND_BASE_IND != 'N'
        );""")

def add_area(df, aoi_split):
    """Selects a BCGW query, dissolves, adds to the AFLB and clips to AOI"""
    # Use Cole's bcgw2gdf to convert the oracle bcgw query to df
    t0 = time()

    # Dissolve and add these to the AFLB geometry
    conn.sql(f"""
    UPDATE aflb_temp
    SET geom = (
        SELECT ST_Union(ST_MakeValid(aflb_temp.geom), ST_MakeValid(add.geom)) AS geom
        FROM vri aflb_temp, 
            (SELECT ST_GeomFromText(wkt) as GEOM FROM {df} where ST_INTERSECTS(GEOM, ST_GeomFromText('{aoi_split}'))) as add
        WHERE ST_Intersects(aflb_temp.geom, ST_GeomFromText('{aoi_split}'))
        )""")
    t1 = time()
    print("{:.2f} s to add square {}/{} to AFLB".format(t1 - t0, count, len(aoi_split_list)))
    
    print("{:.2f}s to add all squares")


def subtract_area(df, aoi_split):
    # remove these from the aflb_temp area
    conn.sql(f"""
    UPDATE aflb_temp
    SET geom = (
        SELECT ST_Difference(ST_MakeValid(aflb_temp.geom), ST_MakeValid(sub.geom)) AS geom
        FROM aflb_temp, 
            (SELECT ST_GeomFromText(wkt) as GEOM FROM {df} where ST_INTERSECTS(GEOM, ST_GeomFromText('{aoi_split}'))) as sub
        WHERE ST_Intersects(aflb_temp.geom, ST_GeomFromText('{aoi_split}')
    )""")
        
    
def identity_area(id_table, field, aoi_split): 
    # Add column
    conn.sql(f"ALTER TABLE aflb_temp ADD COLUMN IF NOT EXISTS {field}")
    # Intersect these with the aflb_temp to create final AFLB layer
    conn.sql(f"""
        CREATE OR REPLACE TABLE AFLB AS (
            SELECT {field}, ST_Area(GEOM)/10000 as AreaHa, GEOM
            FROM (
                SELECT ST_Intersection(ST_MakeValid (aflb_temp.geom), ST_MakeValid(id.geom)) AS GEOM,
                        id.{field} as {field}
                FROM aflb_temp, {id_table} as id
            )
            WHERE ST_Intersects(aflb_temp.geom, ST_GeomFromText('{aoi_split}')
        )""")


#%%
# Get consolidated cut blocks - will include recently harvested areas. 
# Oracle SQL query
cut_osql = f"""
    SELECT SHAPE
    FROM WHSE_FOREST_VEGETATION.VEG_CONSOLIDATED_CUT_BLOCKS_SP
    WHERE SDO_ANYINTERACT (SHAPE,{intersectString}) = 'TRUE'
"""
# Get unioned FWA polygons from BCGW
fwa_osql =  f"""
        SELECT GEOMETRY
        FROM WHSE_BASEMAPPING.FWA_LAKES_POLY
        WHERE SDO_ANYINTERACT (GEOMETRY,{intersectString}) = 'TRUE'
    UNION ALL
        SELECT GEOMETRY
        FROM WHSE_BASEMAPPING.FWA_WETLANDS_POLY
        WHERE SDO_ANYINTERACT (GEOMETRY,{intersectString}) = 'TRUE'
    UNION ALL
        SELECT GEOMETRY
        FROM WHSE_BASEMAPPING.FWA_RIVERS_POLY
        WHERE SDO_ANYINTERACT (GEOMETRY,{intersectString}) = 'TRUE'
        """
# ownership - indicates whether a layer should be AFLB or IFLB. 
own_osql = f"""
    SELECT
        CASE 
            WHEN OWN NOT IN (40, 52, 54, 77, 80, 81, 91, 99) 
            THEN 'AFLB' 
            ELSE 'IFLB' 
        END AS OWN_AFLB,
        GEOMETRY
    FROM WHSE_FOREST_VEGETATION.F_OWN
    WHERE SDO_ANYINTERACT (GEOMETRY,{intersectString}) = 'TRUE'
                """ 
cut_df = bcgw2gdf.get_spatial_table(cut_osql) 
fwa_df = bcgw2gdf.get_spatial_table(fwa_osql) 
own_df = bcgw2gdf.get_spatial_table(own_osql)
# Create ownership layer
conn.sql(f"CREATE TABLE IF NOT EXISTS own AS (SELECT OWN_AFLB, ST_Union_Agg(ST_GeomFromText(wkt)) as GEOM FROM own_df GROUP BY OWN_AFLB)")

#%%
# Create final output table
conn.sql("CREATE TABLE aflb (GEOM GEOMETRY, OWN_AFLB VARCHAR, AreaHa DOUBLE);")
# Loop over AOI split areas
for aoi_split in aoi_split_list:
    get_vri(aoi_split)
    
    conn.sql("CREATE INDEX idx ON vri_temp USING RTREE (geom);")

    
    # Create temp table aflb_temp for operations
    conn.sql("""CREATE OR REPLACE TEMP TABLE aflb_temp AS (
        SELECT GEOM, POLYGON_AREA as AreaHa FROM vri_temp
        )""")
    t0 = time()
    # Add consolidated cutblocks to the AFLB
    add_area('cut_df')
    t1 = time()
    print("{:.2f} s to add square {}/{} to AFLB".format(t1 - t0, count, len(aoi_split_list)))

    # subtract fwa from AFLB
    subtract_area('fwa_df')
    t2 = time()
    print("{:.2f} s to subtract square {}/{} to AFLB".format(t2 - t1, count, len(aoi_split_list)))

    # Subtract agricultural regions?

    # Intersect/Identity the dissolved ownership layer with aflb
    identity_area('own_df', "OWN_AFLB")
    t3 = time()
    print("{:.2f} s to subtract square {}/{} to AFLB".format(t3 - t2, count, len(aoi_split_list)))
    
    # Add this to final AFLB output
    conn.sql("INSERT INTO aflb (SELECT GEOM, OWN_AFLB, AreaHa from aflb_temp)")
    
    
# Clip these by AOI to remove outer polygons
conn.sql(f"""
    UPDATE aflb_temp
    SET geom = (
        SELECT
            CASE WHEN ST_Intersects(geom, ST_Boundary(ST_GeomFromText('{aoi}')))
                    THEN ST_Intersection(geom, ST_GeomFromText('{aoi}'))
                    ELSE geom END
        from aflb_temp v
        );
    """)
t2 = time()
print("{:.2f} s to clip to AOI".format(t2 - t1))
    
    
    
#%%
# Export to shapefile using geopandas
import geopandas as gpd
df = conn.sql(f"SELECT OWN_AFLB, AreaHa, ST_AsText(GEOM) as geometry from AFLB").to_df()
df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
df = gpd.GeoDataFrame(df).set_crs(3005, allow_override=True)

# convert geometry to multipolygon if required
def convertGeom(geom):
    if isinstance(geom, GeometryCollection):
        polygons = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
        return MultiPolygon(polygons) if polygons else None
    else:
        return geom
df['geometry'] = df['geometry'].apply(convertGeom)


df.to_file(outfile)
# %%
