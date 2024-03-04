# BENCHMARKSQL ADAPTATED TO TP README

## 1.adaptator log
### 1.if clone from official tpcc,you'd better run adaptator_tp.sh to increase performance;

## 2.The test process for tp
```
# build tpcc table and optimizer
  ./run/runDatabaseBuild.sh ./run/props.pg
# Run the benchmark
  ./run/runBenchmark.sh ./run/props.pg
# drop all tpcc tables
  ./run/runDatabaseDestroy.sh ./run/props.pg
```

## 3.source
```
  git clone https://github.com/pingcap/benchmarksql.git
```

## 4.use tpcc driver with xtp optimized,same selecti sql will be cached,only used for pk
### 4.1.modify the target configure file ./run/props.pg as follow,jdbc string as target database
```
  driver=org.qianbase.Driver
  conn=jdbc:qianbase://10.14.50.164:20158/qianbase?reWriteBatchedInserts=true
```

### 4.2.rename official jdbc driver with bak,and use qianbase xtp driver qianbase-2.3.3-rc.4.xTP-5-SNAPSHOT-20220906.jar.bak
```
  mv ./lib/postgres/postgresql-9.3-1102.jdbc41.jar ./lib/postgres/postgresql-9.3-1102.jdbc41.jar.bak
  mv ./lib/postgres/qianbase-2.3.3-rc.4.xTP-5-SNAPSHOT-20220906.jar.bak ./lib/postgres/qianbase-2.3.3-rc.4.xTP-5-SNAPSHOT-20220906.jar
```

## 5.tpcc auto run script
### 5.1. tpcc auto script
```
  1. result_directory,must change result directory as target environment;
  2. data_tpcc_source, must generate tpcc warehouse data,and vacuum full,the backup the data directory;
  3. data_tpcc_target, the tp data directory which run by tpcc;
  4. the script will remove and replace the source data directory on every parallel users gradien;
```

### 5.2.run auto script
```
  ./run/tpcc_run.sh
```

## 6.build log table or unlog table
### 6.1.build log table in default,keep as follows:
```  
  vi ./run/runDatabaseBuild.sh 
  #create unlog table
  #BEFORE_LOAD="tableCreatesUnlog"
  # create log table
  BEFORE_LOAD="tableCreates" 
```

### 6.2.build unlog table as follow:
```
  vi ./run/runDatabaseBuild.sh
  #create unlog table
  BEFORE_LOAD="tableCreatesUnlog"
  #create log table
  #BEFORE_LOAD="tableCreates" 
```

