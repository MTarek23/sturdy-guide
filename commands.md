Throughout this guide FireWorks is the workflow management tool while Fireworks are the objects or the atomic computing jobs.

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


## Firework specs

### Definition and good practice
The spec of a Firework completely bootstraps a job and determines what will run. It is advisable to *put any flexible input data as root keys in your spec* and 
*put in the spec any metadata about your job that you want to query on later*.

### Arguments
In the Spec section of yaml files. The instruction to update the spec of all children jobs with some runtime information of the current job is by setting
```bash
_pass_job_info: true
```

## Firetasks

Atomic computing jobs. 

TemplateWriterTask,, FileTransferTask in Yaml files

* `ScriptTask`:  helps run non-Python programs through the command line. If you’d like to instead specify the parameters in the root of the spec, you can set _use_global_spec to True within the _task section. Note that _use_global_spec can simplify querying and communication of parameters between FireWorks but can cause problems if you have multiple ScriptTasks within the same Firework

* `Add and Modify` task  : adds the numbers in the input_array
```bash
- _fw_name: Add and Modify Task
  input_array:
  - 1
  - 1
```

## FWAction

Stores data or modify the Workflow depending on the output (e.g., pass data to the next step, cancel the remaining parts of the Workflow, or even add new FireWorks that are defined within the object).

## Firworker & FireServer

FireWorks can stores Fireworks in the FireServer, but execute them on one or several outside ‘worker’ machine (FireWorkers). A FireWorker is basically the computing resource.
FireServer (“LaunchPad”) manages workflows, the launchpad contains the credentials of your FireServer

## Tips

* In general, using fewer FireWorks is simpler to implement, but less powerful.

* If you cannot connect to the database from a remote worker, you might want to check your Firewall settings and ensure that port 27017 (the default Mongo port) is open/forwarded on the central server.  If you’re still having problems, you can use telnet to check if a port is open: telnet <HOSTNAME> <PORTNAME>, where <HOSTNAME> is your FireServer hostname and <PORTNAME> is your Mongo port (probably 27017).
