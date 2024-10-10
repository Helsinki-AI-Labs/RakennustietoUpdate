Developed with Python 3.10

# Initializing scripts

1. Copy .env from the project you you want to run the scripts against to this directory. Naming follows the Microsoft example repo so a .env
   copied from thre should work out of the box.

```sh
cp ../project/.env .env
```

2. Create venv

```sh
python3 -m venv venv
```

3. Activate venv in the current shell

```sh
source venv/bin/activate
```

4. Initialize venv (repeat this step when adding new packages to requirement.in)

```sh
pip install pip-tools
```

5. Compile requirement.in into requirements.txt

```sh
pip-compile requirements.in
```

6. Install requirements.txt

```sh
pip install -r requirements.txt
```

7. (optional) Point your IDE to the venv
   VSC: Ctrl+Shift+P -> Python: Select Interpreter -> venv/bin/python

# Running scripts

1. Activate venv in the current shell

```sh
source venv/bin/activate
```

2. Run the script

Per project variables are set and loaded from the .env. Some per script variables are set as command line arguments. Such as which directory to upload into etc.

```sh
python create_chunks.py --from_dir ./data --to_dir ./chunks
```
