import duckdb
import os
workingdir = r'C:\Working\WMBAnalysis'
db = os.path.join(workingdir,'vri_analysis.db')
conn = duckdb.connect(database=db)
conn.load_extension("spatial")

conn.sql("""
UPDATE aflb
SET GEOM = clip.GEOM
FROM aflb a_old
INNER JOIN (
    SELECT
        aflb.OBJECTID, 
        ST_Difference(aflb.geom, ST_Union_Agg(fwa.geom)) AS geom
    FROM aflb
        JOIN fwa_simple fwa ON ST_Overlaps(aflb.geom, fwa.geom)
    GROUP BY aflb.OBJECTID, aflb.geom
    ) clip ON a_old.OBJECTID = clip.OBJECTID
         """)
conn.close()