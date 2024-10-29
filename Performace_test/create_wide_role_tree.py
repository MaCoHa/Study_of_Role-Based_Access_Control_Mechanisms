

import os
import time
import snowflake.connector
import sql.wide_role_sql as sql
import utils as util
import psycopg2 

def create_connection(database_name, schema_name):
    password = os.getenv('SNOWSQL_PWD')

    snowflake_config = {
        "user": "CAT",
        "password": password,
        "account": "sfedu02-gyb58550",
        "database": database_name,
        "schema": schema_name,
        "session_parameters": {
            "USE_CACHED_RESULT": False
        }
    }

    return snowflake_config


def use_warehouse(cur, warehouse):
    cur.execute(f"use warehouse {warehouse}")

def main(repetitions,time_limit_minutes,file_name,db):
    
    if db == "Snowflake":
        print('Connecting to the Snowflake database...') 
        
        connection_config = create_connection("WIDE_ROLE_DB", "PUBLIC")
        conn = snowflake.connector.connect(**connection_config)
        cur = conn.cursor()
        use_warehouse(cur, "ANIMAL_TASK_WH")
    elif db == "PostgreSql":
        print('Connecting to the PostgreSQL database...') 
        
        params = util.postgres_config(section='postgresql_Wide') 
        # connect to the PostgreSQL server 
        conn = psycopg2.connect(**params) 
        cur = conn.cursor() 
    else:
        print('Connecting to the MariaDB database...') 
        print('********************* TODO *********************') 
        return
        
        

    util.remove_roles(db,cur,conn,61255)
    cur.close
    conn.close
    return

    time_limit_seconds = time_limit_minutes * 60

    util.create_log_initial(file_name)
    
    try:
        print("Running wide role tree")
        
        # Run create roles
        print("Running Create Roles")
        for i in range(repetitions):
            
            if i < (repetitions - 1):
                print(f"Running repetition {1+i} out of {repetitions}", end="\r")
            else:
                print(f"Running repetition {1+i} out of {repetitions}")
                
            start_time = time.time()
            role_num = 1
            while True:
                # Check the elapsed time
                elapsed_time = time.time() - start_time
                if elapsed_time > time_limit_seconds:
                    print("Time limit reached. Exiting loop.")
                    break
                
                for query in sql.generate_role_queries(db,f"Role{role_num}"):
                    start_query_time = time.perf_counter_ns() / 1_000_000 # convert from ns to ms
                    cur.execute(query)
                    end_query_time = time.perf_counter_ns() / 1_000_000 # convert from ns to ms
                    util.append_to_log(file_name,
                            [query,
                            db,
                            "Wide_tree",
                            i,
                            role_num,
                            (start_query_time),
                            (end_query_time)])
                    
                if db == "PostgreSql":
                    conn.commit()
                
                
                role_num += 1
                
            # run clean up roles            
            util.remove_roles(db,cur,conn,role_num)
         
    finally:
        conn.close()
        cur.close()
