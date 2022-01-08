import io
import re
import sys
import time
import logging
import pathlib
import argparse
from configparser import ConfigParser
from datetime import datetime, timedelta



import requests
import schedule
import psycopg2 as db

# Regular expression to filter only valid data
# indexes:                     0 Month         1 Day                   2 Year      3 Hour      4 Min       5 Sec       6 Id        7 Line      8 Lat            9 Lon           10 speed
dataFormat = re.compile(r"""^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])-(\d{4})\s([012][0-9]):([0-5][0-9]):([0-5][0-9]),(\w\d{2,5}),([\d\w]*),"(\-+\d{2}\.\d*)","(\-+\d{2}\.\d*)",(\d*)$""",flags=re.MULTILINE)

def CollectBusData(database, logger=logging):
    
    # Check database connectivity
    if database.closed:
        try:
            database.reset()
        except:
            raise Exception("Connection was broken and couldn't be reastablished")

    # Collects data from city's API
    response = requests.get("http://dadosabertos.rio.rj.gov.br/apiTransporte/apresentacao/csv/onibus.cfm")
    if response.status_code != 200:
        raise Exception(f"API page returned code {response.status_code}")
    
    rawBusData = response.text
    
    logger.debug("Filtering raw data")

    validData = dataFormat.findall(rawBusData)
    
    if len(validData) == 0:
        raise Exception("No data was retrieved from server")

    logger.debug("Exctracting unique days")

    dates = set([f"{i[2]}-{i[0]}-{i[1]}" for i in validData])

    cleanDates = [(datetime.fromisoformat(i),datetime.fromisoformat(i) + timedelta(hours=23,minutes=59,seconds=59)) for i in dates]

    logger.debug("Creating new partitions on table")
    # Issues creation of new partitions if they don't exist
    
    for lowerLimit, upperLimit in cleanDates:
		# New partition creation
        logger.debug(f"\t'-> Issuing new partition for time range of {lowerLimit} to {upperLimit}")
        try:
            with database.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS 
                        bus_data_{lowerLimit.year}_{lowerLimit.month}_{lowerLimit.day} 
                    PARTITION OF bus_data 
                    FOR VALUES FROM ('{lowerLimit.isoformat()}') TO ('{upperLimit.isoformat()}')""")
                database.commit()
        except:
            raise Exception("""Failed to issue "CREATE TABLE ... PARTITION OF" to database""")

    lineDec = '\\N'
    with io.StringIO() as buffer:
        for item in validData:
            lineId = item[7] if len(item[7]) > 0 else '\\N'
            buffer.write(f"""{item[2]}-{item[0]}-{item[1]} {item[3]}:{item[4]}:{item[5]},{item[6]},{item[8]},{item[9]},{lineId},{lineDec}\n""")
        buffer.seek(0)
        logger.debug("Sending to database")
        try:
            with database.cursor() as cursor:
                cursor.copy_from(buffer,'bus_data',sep=',')
                database.commit()
        except:
            raise Exception("Failed to send data to database")


    logger.info(f"Added {len(validData)} entries")

if __name__ == "__main__":

    # References to different functions based on desired mode
#    ImplementedModes = {
#        'bus':s#,
    #    'lines':mainLines,
#        'get_lines':mainGetLines
    #}

    #FilesDir = pathlib.Path("/var/run/secrets")
    #DefaultConfigurationsFile = FilesDir/ "main_configurations"
    #DatabaseCredentialsFile = FilesDir/ "db_credentials"
    # -------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Script to write data to database")
#    parser.add_argument("mode",type=str,choices=ImplementedModes.keys(),help='Mode selection (bus/line)')
#    parser.add_argument('-c',"--config",default=DefaultConfigurationsFile,type=pathlib.Path,help="Configuration file full path")
#    parser.add_argument('-d',"--date",type=datetime.date.fromisoformat,default=None,help="Desired date for single mode data insertion (YYYY-MM-DD)")
#    parser.add_argument('-m',"--multi",nargs="+",help="Execute same command for multiple dates/files given as option values")
    parser.add_argument("-v",'--verbose',action="count",default=0,help="Increase output verbosity")
    parser.add_argument('--database-credentials',type=pathlib.Path,help="File containing all database credentials")
#    parser.add_argument("-b","--bus",default=None,help='bus data insertion path')
#    parser.add_argument("-l","--line",default=None,help='bus data insertion path')
#    parser.add_argument("--csv",action='store_true',help="outputs data as csv file instead of sending to database")
    parser.add_argument("-r","--repeat",action='store_true',help="Keeps running continuoulsy, repeats call to API each 60 seconds")
    args = parser.parse_args(sys.argv[1:])
    
    DatabaseCredentialsFile = args.database_credentials
    # ----------------------------------------
    # Logger definition
    # ---------------------------------------

    logger = logging.getLogger(sys.argv[0])
    logger.setLevel(logging.DEBUG)
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    
    logLevel = logging.ERROR * (args.verbose == 0) + \
                logging.WARNING * (args.verbose == 1) + \
                logging.INFO * (args.verbose == 2) + \
                logging.DEBUG * (args.verbose >= 3)

    ch.setLevel(logLevel)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
     
    # --------------------------------
    # Configuration parameters gathering
    # --------------------------------
    
    logger.debug("Logging initialized")
    # Config object creation
    CONFIGS = ConfigParser()
    
    # As a container, set default paths
#    CONFIGS.add_section('paths')
#    CONFIGS['paths']['importBusPath'] = '/collect_bus_old/' if args.bus is None else args.bus
#    CONFIGS['paths']['importLinePath'] = '/collect_line/' if args.line is None else args.line

    # Collects compatible variables from environment
#    CONFIGS.add_section('database')
#    if os.getenv("DATABASE_USERNAME"):
#        CONFIGS['database']['user'] = os.getenv("DATABASE_USERNAME")
#    if os.getenv("DATABASE_PASSWORD"):
#        CONFIGS['database']['password'] = os.getenv("DATABASE_PASSWORD")
#    if os.getenv("DATABASE_NAME"):
#        CONFIGS['database']['database'] = os.getenv("DATABASE_NAME")
#    if os.getenv("DATABASE_HOST"):
#        CONFIGS['database']['host'] = os.getenv("DATABASE_HOST")

    # Read configs from main_configurations
    #logger.debug(f"Reading configs from {args.config}")
    #CONFIGS.read(args.config)

    # If database credentials set on another file, overwrites previously found credentials
    if DatabaseCredentialsFile:
        logger.debug(f"Reading database credentials from {DatabaseCredentialsFile}")
        CONFIGS.read(DatabaseCredentialsFile)
    
    if not CONFIGS.has_section("database"):
        logger.critical("No database credentials where found")
        exit(1)

    missingOptions = {"user","password","host","database"}.difference([ i for i in CONFIGS['database'].keys()])
    
    if len(missingOptions):
        logger.critical(f"Missing critical database options: {missingOptions}")
        exit(1)

    # --------------------------------------------------------------------
    # Database connection
    # --------------------------------------------------------------------
    #logger.info(f"Database connection attempt at '{CONFIGS['database']['database']}':")
    #logger.info(f"\tLogin attempt: '{CONFIGS['database']['user']}'@'{CONFIGS['database']['host']}'")
    #logger.info(f"""\t{"password set" if CONFIGS.has_option("database","password") else "password NOT set"}""")
#    CONFIGS.add_section('output') 
#    CONFIGS['output']['csv'] = 'true' if args.csv else 'false'

    # Establishing database connection
#    if args.mode == 'get_lines':
#         database = None
#    else:
    
    try:
        database = db.connect(**CONFIGS['database'])
    except Exception as err:
        logger.critical("Could not connect to database")
        exit(1)

    #logger.info("Connection successful.")
    #logger.info(f"Selected mode: {args.mode}")

    #logger.debug(f"""Other params: verbose = '{args.verbose}'/ config = '{args.config}' / date = '{args.date}' """)
    
    
    if not args.repeat:
        CollectBusData(database,logger)
        exit(0)
    
    schedule.every().minute.do(CollectBusData,database,logger)
    
    while True:
        try:
            schedule.run_pending()
        except Exception as err:
            logger.error(f"Failed to collect data - {err}")
           
        time.sleep(2)

