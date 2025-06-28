#%%
# Import libraries
import sys
import duckdb
import fiona
import os
from shapely.geometry import shape, MultiPolygon, Polygon, GeometryCollection
from time import time

sys.path.append("\\spatialfiles2.bcgov\work\FOR\RNI\DPC\General_User_Data\nross\BRFN_NE_LUPCE_Analysis\scripts\WMB_Analysis")
from bcgw2gdf import bcgw2gdf

bcgw2gdf = bcgw2gdf()


vri_url = "https://nrs.objectstore.gov.bc.ca/rczimv/geotest/veg_comp_layer_r1_poly.parquet"
# aoi_path = r'\\spatialfiles.bcgov\work\srm\nr\NEGSS\NEDD\First_Nations_Agreements\BRFN_Implementation_Agreement\Shapefiles\CameronWMB.shp'
aoi_path = r'\\spatialfiles2.bcgov\work\FOR\RNI\DPC\General_User_Data\nross\BRFN_NE_LUPCE_Analysis\WMB_Study_Area_2024_07_30\WMB_Study_Area_2024_07_30.shp'
workspace = r'C:\Users\nross\OneDrive - Government of BC\Documents\BRFNDocs\aflb-test'
outfile = os.path.join(workspace, 'shp', 'aflb.shp')

# Connect to Duckdb in-memory and load extensions
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
    print(round(aoi_area_ha, 2))
    
# define Oracle SQL string for intersecting with the bounds of the AOI
intersectString = f"""
SDO_GEOMETRY(2003, 3005, NULL,
        SDO_ELEM_INFO_ARRAY(1,1003,3),
        SDO_ORDINATE_ARRAY{aoiBoundsStr} 
    )
"""
def add_area(sql):
    """Selects a BCGW query, dissolves, adds to the AFLB and clips to AOI"""
    # Use Cole's bcgw2gdf to convert the oracle bcgw query to df
    df = bcgw2gdf.get_spatial_table(sql) 
    t0 = time()
    
    #Split
    # Dissolve and add these to the AFLB geometry
    conn.sql("""
    UPDATE aflb_temp
    SET geom = (
        SELECT ST_Union(ST_MakeValid(aflb_temp.geom), ST_MakeValid(add.geom)) AS geom
        FROM aflb_temp, 
            (SELECT ST_Union_Agg(ST_GeomFromText(wkt)) as GEOM FROM df GROUP BY ALL) as add
        )""")
    t1 = time()
    print("{:.2f} s to add AFLB".format(t1 - t0))
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
    del df

def subtract_area(sql):
    # Use Cole's bcgw2gdf to convert the oracle bcgw query to df
    df = bcgw2gdf.get_spatial_table(sql) 

    # remove these from the aflb_temp area
    conn.sql("""
    UPDATE aflb_temp
    SET geom = (
        SELECT ST_Difference(ST_MakeValid(aflb_temp.geom), ST_MakeValid(sub.geom)) AS geom
        FROM aflb_temp, 
            (SELECT ST_Union_Agg(ST_GeomFromText(wkt)) as GEOM FROM df GROUP BY ALL) as sub
    )""")
    del df
    
def identity_area(sql, field):
    # Use Cole's bcgw2gdf to convert the oracle bcgw query to df
    df = bcgw2gdf.get_spatial_table(sql) 
    
    # Dissolve these on ownership and import to duckdb
    conn.sql(f"CREATE TABLE IF NOT EXISTS id AS (SELECT {field}, ST_Union_Agg(ST_GeomFromText(wkt)) as GEOM FROM df GROUP BY {field})")

    # Intersect these with the aflb_temp to create final AFLB layer
    conn.sql(f"""
        CREATE OR REPLACE TABLE AFLB AS (
            SELECT {field}, ST_Area(GEOM)/10000 as AreaHa, GEOM
            FROM (
                SELECT ST_Intersection(ST_MakeValid (aflb_temp.geom), ST_MakeValid(id.geom)) AS GEOM,
                        id.{field} as {field}
                FROM aflb_temp, id
            )
        )""")
    conn.sql("DROP TABLE id")

#%%
# Create dissolved VRI table in Duckdb. Download VRI from Parquet object. 
# See https://github.com/bcgov/gis-pantry/blob/0bb91df02b6c8fe00f4914679e3804ba71ea9020/recipes/duckdb/duckdb-geospatial.ipynb
conn.sql(f"""
    CREATE TABLE IF NOT EXISTS vri as (
        SELECT ST_Union_Agg(Shape) as geom, SUM(POLYGON_AREA) as POLYGON_AREA
        FROM '{vri_url}' -- read parquet file from objectstorage
        WHERE 
            ST_Intersects (Shape, ST_GeomFromText('{aoi}'))
        AND
            BCLCS_LEVEL_1 != 'N' AND BCLCS_LEVEL_2 != 'W' AND BCLCS_LEVEL_3 != 'W'
        AND
            FOR_MGMT_LAND_BASE_IND != 'N'
    );""")
#%%
# Create temp table aflb_temp for operations
conn.sql("""CREATE TEMP TABLE aflb_temp AS (
    SELECT ST_Simplify(GEOM, 1) AS GEOM, "SUM(POLYGON_AREA)" as AreaHa FROM vri
    )""")
#%%
# Get consolidated cut blocks - will include recently harvested areas. 
# Oracle SQL query
cut_osql = f"""
    SELECT SHAPE
    FROM WHSE_FOREST_VEGETATION.VEG_CONSOLIDATED_CUT_BLOCKS_SP
    WHERE SDO_ANYINTERACT (SHAPE,{intersectString}) = 'TRUE'
"""
# Add this to the AFLB
add_area(cut_osql)
#%%
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
# subtract these from AFLB
subtract_area(fwa_osql)
#%%
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
# Intersect/Identity this with the final output
identity_area(own_osql, "OWN_AFLB")
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
