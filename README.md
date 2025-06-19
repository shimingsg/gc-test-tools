# gc-test-tools

## usage
```bash
python run.py -r <local path of runtime repo> -a
```

## get help info
```bash
python run.py --help
```

## what the script does:
- [x] git pull to get lastest code from dotnet/runtime repo
- [x] build clr + libs + test layout
- [x] build gc individual tests
- [x] run tests
- [x] summary

## TO DO
- [x] worflow
- [ ] re-run failed test
- [ ] collect re-run result
- [ ] complete summary report (Reproducible)
