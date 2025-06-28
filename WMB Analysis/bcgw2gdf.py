# BCGW2GDF
# import geopandas as gpd
import pandas as pd
import oracledb
import logging
import json

#set up logging 
logging.basicConfig(level=logging.DEBUG)
debug=logging.debug
info=logging.info
warning=logging.warning
error=logging.error

# class set up
# +-------------------------------------------------------------------------------------------------
class bcgw2gdf:

    def __init__(self):
        self.dbname = "BCGW"
        self.cnxinfo = self.get_db_cnxinfo()
        
    def get_db_cnxinfo(self):
        """ Retrieves db connection params from the config file"""
        with open(r'H:\config\db_config.json', 'r') as file:
            data = json.load(file)
        
        if self.dbname in data:
            return data[self.dbname]
        
        raise KeyError(f"Database '{self.dbname}' not found.")
# BCGW connection
# call to create oracle connection and engine used in getting the bcgw layer  
# +-------------------------------------------------------------------------------------------------
    def bcgw_connect(self):

        conn=oracledb.connect(user = self.cnxinfo['username'], 
                                password = self.cnxinfo['password'], 
                                dsn = self.cnxinfo['hostname'])
          
        # get layers function
        # +-------------------------------------------------------------------------------------------------
    #function to turn sql query into geodataframe 
    def get_spatial_table(self,sql_query):
        conn=oracledb.connect(user = self.cnxinfo['username'], 
                            password = self.cnxinfo['password'], 
                            dsn = self.cnxinfo['hostname'])   
        #create cursor and excecute sql
        cursor = conn.cursor()
        cursor.execute(sql_query)
        #query to pandas
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        # under try are the most common geom columns, while the except are the more obscure ones
        try:
            if 'SHAPE' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(SHAPE) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('SHAPE', axis=1)
            elif 'GEOMETRY' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(GEOMETRY) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('GEOMETRY', axis=1)
        except:
            if 'EXTENT' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(EXTENT) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('EXTENT', axis=1)
            elif 'LEGACY_CS_BOUNDS' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(LEGACY_CS_BOUNDS) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('LEGACY_CS_BOUNDS', axis=1)
            elif 'SDO_ROOT_MBR' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(SDO_ROOT_MBR) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('SDO_ROOT_MBR', axis=1)
            elif 'BLOCKMBR' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(BLOCKMBR) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('BLOCKMBR', axis=1)
            elif 'CS_BOUNDS' in df.columns:
                cursor.execute(f"SELECT SDO_UTIL.TO_WKTGEOMETRY(CS_BOUNDS) FROM ({sql_query})")
                wkb_data = cursor.fetchall()
                df['wkt'] = [val[0].read() if val[0] else None for val in wkb_data]
                df = df.drop('CS_BOUNDS', axis=1)    
        # Close cursor and connection
        cursor.close()
        conn.close()
        #make wkt readable by gpd by using a geoseries and the function from_wkt
        # df['wkt']=gpd.GeoSeries.from_wkt(df['wkt'])
        # gdf=gpd.GeoDataFrame(df, geometry='wkt')
        # #set crs to bc albers
        # gdf = gdf.set_crs(3005, allow_override=True)
        info('spatial query returned as GeoDataFrame')
        return df