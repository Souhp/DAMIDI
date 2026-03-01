
# DAMIDI

# Midireader app

## Run the app


plz use: python 3.12.8

*PS a lot of things in the requirements txt are not nessisary to run the app it just happens to be in my pip freeze and I havent spend the time optimizing the list srry for the long download.:(*

*FYI You must go through and remove some obsolete packages when pasting from requirements to TOML when building the app atm.*




Run as a desktop app:


```
flet run
```

If your linux distro does not like flets gui
Run as a web app:

```
flet run --web
```

### Poetry

Install dependencies from `pyproject.toml`:

```
poetry install
```

Run as a desktop app:

```
poetry run flet run
```

Run as a web app:

```
poetry run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/getting-started/).

## Build the app


### Linux

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### Windows

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).

