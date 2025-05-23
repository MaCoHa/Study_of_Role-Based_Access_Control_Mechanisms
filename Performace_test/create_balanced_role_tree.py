

import datetime
import os
import sys
import time
import mariadb
import snowflake.connector
import sql.balanced_role_sql as sql
import utils as util
import psycopg2 




def main(repetitions,time_limit_minutes,file_name,db):
    
    if db == "Snowflake" or db == "Snowflake_EC2":
        #print('Connecting to the Snowflake database...') 
        
        connection_config = util.create_connection("RBAC_EXPERIMENTS", "ACCOUNTADMIN")
        conn = snowflake.connector.connect(**connection_config)
        cur = conn.cursor()
        util.use_warehouse(cur, "ANIMAL_TASK_WH")
    elif db == "PostgreSql":
        #print('Connecting to the PostgreSQL database...') 
        
        # connect to the PostgreSQL server 
        conn = util.postgres_config()
        # autocommit commits querys to the database imediatly instead of
        #storing the transaction localy
        conn.autocommit = True
        cur = conn.cursor() 
    elif db == "PostgreSql_EC2":
        #print('Connecting to the PostgreSQL database...') 
        
        # connect to the PostgreSQL server 
        conn = util.postgres_config_remote()
        # autocommit commits querys to the database imediatly instead of
        #storing the transaction localy
        conn.autocommit = True
        cur = conn.cursor() 
        

    elif db == "MariaDB":
        # connect to the MariaDB server   
        #print('Connecting to the MariaDB database...') 
        try:
            # connect to the MariaDB server 
            conn = util.mariadb_config() 
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        cur = conn.cursor()

    elif db == "MariaDB_EC2":
        # connect to the MariaDB server   
        #print('Connecting to the MariaDB database...') 
        try:
            # connect to the MariaDB server 
            conn = util.mariadb_config_remote() 
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        cur = conn.cursor()

    
    test_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        

    time_limit_seconds = time_limit_minutes * 60

    util.create_log_initial(file_name)
    
    try:
        #print(f"Running balanced role tree on {db}")
        
        # Run create roles
        #print("Running Create Roles")
        for i in range(repetitions):
           
            start_time = time.time()
            current = 0
            front = 1
            while True :
                
                
                elapsed_time = time.time() - start_time
                if elapsed_time > time_limit_seconds:
                    print("Time limit reached. Exiting loop.")
                    break
                            
    
                for query in sql.generate_role_queries(db,f"Role{current}",f"Role{(front)}"):
                    start_query_time = time.perf_counter_ns() / 1_000_000  # convert from ns to ms
                    cur.execute(query)
                    end_query_time = time.perf_counter_ns() / 1_000_000  # convert from ns to ms

                    #HERE — Now with verification and logging of success/failure
                    util.append_to_log(file_name,
                        [test_id,
                            query.replace(";", ""),
                            db,
                            "balanced_tree",
                            i,
                            front,
                            start_query_time,
                            end_query_time,
                            ])

                                
        
            
        
                
                if (front % 4) == 0:
                    current += 1
                front += 1
               
                
            # run clean up roles  
            #util.remove_roles(db,cur,front)
            util.remove_roles_log(db,cur,front,file_name,test_id,i,"balanced_tree")

  
                

    finally:
        conn.close()
        cur.close()
