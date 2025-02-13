<p align="center">
    <img src="https://raw.githubusercontent.com/Ascentrade/docs/main/assets/icon_plain.svg" alt="Ascentrade Logo"/>
</p>

# Ascentrade Backend

This repository provides an external REST API and an internal GraphQL API.
The Ascentrade [database](https://github.com/Ascentrade/database) provides the data.

## Virtual Environment
Create a virtual Python 3.10 environment and activate + install all dependencies.
```
python3.10 -m venv venv
source venv/bin/activate
pip3.10 install -r requirements.txt
```

## Usage

1. Start the [database](https://github.com/Ascentrade/database) with `docker` or `podman`:

        sudo docker run --daemon --name database \
        --environment POSTGRES_PASSWORD=postgres \
        --environment POSTGRES_DB=database \
        --volume path/to/database/sql/:/docker-entrypoint-initdb.d/:Z \
        postgres:alpine

    or
    
        podman run --daemon --name database \
        --environment POSTGRES_PASSWORD=postgres \
        --environment POSTGRES_DB=database \
        --volume path/to/database/sql/:/docker-entrypoint-initdb.d/:Z \
        postgres:alpine

2. Use the [`Dockerfile`](./Dockerfile) to build the backend with all dependencies:

        sudo docker build . -t backend

    or

        podman build . -t backend

3. Start the backend:

        sudo docker run --daemon --name backend \
        --env-file .env.template \
        --volume ./:/src/:Z \
        --ports 127.0.0.1:8000:8000

    or

        podman run --daemon --name backend \
        --env-file .env.template \
        --volume ./:/src/:Z \
        --ports 127.0.0.1:8000:8000

4. After startup, you can access the Ariadne GraphQL interface at http://localhost:8000/graphql

## Contributing

We encourage public contributions! Please review [CONTRIBUTING.md](https://github.com/Ascentrade/docs/blob/main/CONTRIBUTING.md) for details.

## License

<p align="center">
    <img src="https://www.gnu.org/graphics/agplv3-with-text-162x68.png" alt="GNU Affero General Public License Version 3"/>
</p>

```
Copyright (C) 2024 Dennis Greguhn and Pascal Dengler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

See [LICENSE](./LICENSE) for more information.