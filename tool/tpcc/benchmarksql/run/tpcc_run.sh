##############################################3
###
 # @Author: xin.zhao@esgyn.cn
 # @Date: 2023-09-08 17:13:43
 # @LastEditors: Do not edit
 # @FilePath: \performance_everydayc:\code\liusongsong\performance_tpcc_everyday\tool\tpcc\benchmarksql\run\tpcc_run.sh
 # @version: 1.0.0
### 
#1. used for test tpcc performance on different threads,not for daily
#2. tpcc config file as $config_file
#2. must start nmon by manually
##############################################

#!/bin/bash

result_directory=$1
result_name_flag=$2
data_tpcc_source=$3
data_tpcc_target=$4
database=$5
warehouses=$6
preheat=$7
number=$8

threads=("1" "20" "50")

config_file=props.test

#prepare tp data directory,and must do vacuum full on data_tpcc_source
function tpcc_prepare
(
    if ([ -d ${data_tpcc_source} ]);then
        echo "tp instance stop ..."
        qctl -D ${data_tpcc_target} stop
        if [ -d ${data_tpcc_target} ];then
            echo "clean data on ${data_tpcc_target} ..."
            rm -rf ${data_tpcc_target}/*;
        fi
        ls -lrt ${data_tpcc_target}
        echo "copy data directory from ${data_tpcc_source} to ${data_tpcc_target} ..."
        cp -r ${data_tpcc_source}/* ${data_tpcc_target}/
        ls -lrt ${data_tpcc_target}
        echo "tp instance start..."
        qctl -D ${data_tpcc_target} start
        echo "analyze tpcc..."
        qsql -d ${database} -c "vacuum analyze;";
    else
        exit;
    fi
)


function check_tpcc_data_consistency
(
    queries=("(select w_id, w_ytd from bmsql_warehouse) except(select d_w_id, sum(d_ytd) from bmsql_district group by d_w_id);"  # Query 1
             "(select d_w_id, d_id, D_NEXT_O_ID - 1 from bmsql_district) except (select o_w_id, o_d_id, max(o_id) from bmsql_oorder group by o_w_id, o_d_id);"  # Query 2
             "(select d_w_id, d_id, D_NEXT_O_ID - 1 from bmsql_district) except (select no_w_id, no_d_id, max(no_o_id) from bmsql_new_order group by no_w_id, no_d_id);" # Query 3
             "select * from (select (count(no_o_id)-(max(no_o_id)-min(no_o_id)+1)) as diff from bmsql_new_order group by no_w_id, no_d_id) as foo where diff != 0;" # Query 4
             "(select o_w_id, o_d_id, sum(o_ol_cnt) from bmsql_oorder group by o_w_id, o_d_id) except (select ol_w_id, ol_d_id, count(ol_o_id) from bmsql_order_line group by ol_w_id, ol_d_id);" # Query 5
             "(select d_w_id, sum(d_ytd) from bmsql_district group by d_w_id) except(Select w_id, w_ytd from bmsql_warehouse);"  # Query 6
            )

    for query in "${queries[@]}"; do
        result=$(qsql -d ${database} -c "$query")
        grep_result=$(echo "$result" | grep rows)
        if [ "$grep_result" != "(0 rows)" ]; then
            echo "$query"
            echo "Data inconsistency detected???: $result"
            exit 1  
        fi
    done
    echo "data consistency!!!"
)

function tpcc_run_nopreheat
(
    # run 1times
    for((id=1;id<=${number};id++))
    do
        tpcc_prepare;
        sleep 120;
        # sleep 60;
        current_date=$(date +%Y%m%d%H%M%S)
        echo "start running tpcc ${1} theads ${id} times..."
        sed -i "s/terminals=[0-9]*/terminals=${1}/g"  ${config_file}
        ./runBenchmark.sh ${config_file} |tee -a ${result_directory}/tpcc_${warehouses}warehouse_${result_name_flag}_${1}threads_${current_date}.log
        echo "${result_directory}/tpcc_${warehouses}warehouse_${result_name_flag}_${1}threads_${current_date}.log" >> ${result_directory}/log_tpcc_list
        echo "${result_directory}/tpcc_${warehouses}warehouse_${result_name_flag}_${1}threads_${current_date}.log"
        # sleep 60
        # cp tpcc_1000warehouse_${result_name_flag}_${1}threads_${current_date}.log ${result_directory}/;
        sleep 300;
        # sleep 120;

        check_tpcc_data_consistency;
    done
)

function tpcc_run_preheat
(
    # run 1times
    for((id=1;id<=${number};id++))
    do
        sleep 120;
        # sleep 60;
        current_date=$(date +%Y%m%d%H%M%S)
        echo "start running tpcc ${1} theads ${id} times..."
        sed -i "s/terminals=[0-9]*/terminals=${1}/g"  ${config_file}
        ./runBenchmark.sh ${config_file} |tee -a ${result_directory}/tpcc_${warehouses}warehouse_${result_name_flag}_${1}threads_${current_date}.log
        echo "${result_directory}/tpcc_${warehouses}warehouse_${result_name_flag}_${1}threads_${current_date}.log" >> ${result_directory}/log_tpcc_list
        echo "${result_directory}/tpcc_${warehouses}warehouse_${result_name_flag}_${1}threads_${current_date}.log"
        # sleep 60
        # cp tpcc_1000warehouse_${result_name_flag}_${1}threads_${current_date}.log ${result_directory}/;
        sleep 300;
        # sleep 120;
        check_tpcc_data_consistency;
    done
)

function run_nopreheat()
(
    echo "" > ${result_directory}/log_tpcc_list
    for thread in "${threads[@]}"; do
        tpcc_run_nopreheat $thread
    done
)

function run_preheat()
(
    echo "" > ${result_directory}/log_tpcc_list
    for thread in "${threads[@]}"; do
        tpcc_prepare
        tpcc_run_preheat $thread
    done
)

if [ $preheat = "true" ]; then
    echo "run_preheat : ${preheat}"
    run_preheat
else
    echo "run_nopreheat : ${preheat}"
    run_nopreheat
fi


