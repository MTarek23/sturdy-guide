## Adding/Validating/Visualising Workflows

Check added workflow for errors
```bash
lpad check_wflow -i <firework ID>
```
add and check simultaneously
```bash
lpad add -c <workflow name>
```
Adds workflow (yaml/json file)
```bash
lpad add <workflow name>					
```
Delete workflow
```bash
lpad delete_wflows -i <workflow ID>
```
Query the database (info about fireworks)
```bash
lpad get_fws [-i <firework ID>] [-d <more|all>]
     -s  status
```
Query workflows
```bash
lpad get_wflows
```

Produce output in yaml format instead of json
```bash
lpad -o yaml
```
Print a table of the current status
```bash
lpad -o yaml get_wflows -t -m 10 --rsort created_on 
```

Visualize Workflow to in a pdf
```bash
lpad check_wflow -i <workflow ID> [-g <controlflow | dataflow | combined>] [-f <workflow name>]
     dot -Tpdf -o <pdf name>.pdf <workflow name>.dot
```

## Troubleshooting

Rerun problematic fws if problem is external (doesn't modify children's specs)
```bash
lpad rerun_fws -i <firework ID>
```

if the error is in the spec
```bash
lpad update_fws -i <firework ID> -u '{<update>}'
```
## Launching fireworks

Fetch availble fireworks from the server and runs it one at a time
```bash
rlaunch singleshot
```

Launch rockets, will keep repeating until we run out of FireWorks to run
```bash
rlaunch rapidfire
	-nlaunches infinite --sleep $number	## looks for new FWs every $number seconds
	-silencer				## suppresses log messages/verbose
```
Launch fireworks in parallel
```bash
rlaunch multi
```

## Firetasks

TemplateWriterTask, ScriptTask, FileTransferTask in Yaml files

* `Add and Modify` task  : adds the numbers in the input_array
```bash
    - _fw_name: Add and Modify Task
    input_array:
    - 1
    - 1
 ```

## Other spec arguments

In the Spec section of yaml files. The instruction to update the spec of all children jobs with some runtime information of the current job is by setting
```bash
_pass_job_info: true
```
