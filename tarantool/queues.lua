#!/usr/bin/env tarantool

-- Configure database
box.cfg {
    listen = 3313,
--    background = true,
--    work_dir = './data/tarantool',
--    wal_dir = 'xlog_wal',
--    memtx_dir = 'snapshot_memtx'
    log='/var/lib/tarantool/tarantool_queue.txt',
    pid_file = '/var/lib/tarantool/tarantool_queue.pid'
}

-- add a log record on task completion
log = require('log')
local function otc_cb(task, stats_data)
    if stats_data == 'delete' then
        log.info("task %s is done", task[1])
    end
end

queue = require('queue')
queue.create_tube('fifo_texts', 'fifo', {temporary = true, on_task_change = otc_cb, if_not_exists = true})
queue.tube.fifo_texts:put({
    text = 'tarantool queue started ' .. os.date("%Y-%m-%d %H:%M:%S"),
    n_errors = null
})

-- print('Starting ', arg[1])
