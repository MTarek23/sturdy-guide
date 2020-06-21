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
*** lpad add <workflow name>					
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
lpad check_wflow -i <workflow ID> [-g <controlflow | dataflow | combined>] [-f <filename>]
     dot -Tpdf -o <pdf name>.pdf <workflow name>.dot
```
