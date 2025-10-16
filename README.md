# Divia-Transport-Planner

A comprehensive route planning system for the "DiviaMobilités" public transportation network using GTFS data, NetworkX graph algorithms, and AI-powered assistance.

## Dataset

**Sources**:
 - [gtfs-diviamobilites](https://transport.data.gouv.fr/datasets/gtfs-diviamobilites)
 - [gfts-documentation-routestxt](https://gtfs.org/documentation/schedule/reference/#routestxt)

### Details

- Network: KEOLIS DIJON
- Transport modes: bus, tramway
- Number of lines: 57
- Number of stops: 1 086
- Number of stop areas: 0

### Files dataset overview

<table> <thead> <tr> <th>Fichier</th> <th>Role / Description</th> </tr> </thead> <tbody> <tr> <td><strong>agency.txt</strong></td> <td>Contains the transit agency/operator (e.g., DiviaMobilités): name, URL, timezone, etc.</td> </tr> <tr> <td><strong>stops.txt</strong></td> <td>Describes stops or stations: identifier, name, geographical coordinates, type, and more.</td> </tr> <tr> <td><strong>routes.txt</strong></td> <td>Lists all routes in the network: ID, short/long name, color, type (bus, tram, etc.).</td> </tr> <tr> <td><strong>trips.txt</strong></td> <td>Details each operational service on a route: for every “trip” (a journey/instance), associates with a route and a calendar service.</td> </tr> <tr> <td><strong>stop_times.txt</strong></td> <td>Specifies, for each trip, the sequence of stops served and the scheduled times (arrival/departure) at each stop.</td> </tr> <tr> <td><strong>calendar.txt</strong></td> <td>Defines the days/hours when services are operational (per service_id): active from Monday to Sunday, start and end dates, etc.</td> </tr> <tr> <td><strong>shapes.txt</strong></td> <td>Provides the precise geographical path of routes/trips as a sequence of points (for detailed mapping).</td> </tr> </tbody> </table>

**Route type mapping (from GTFS documentation)**:

<table> <thead> <tr> <th>Value</th> <th>Description</th> </tr> </thead> <tbody> <tr><td>0</td><td>Tram, Streetcar, Light rail</td></tr> <tr><td>1</td><td>Subway, Metro</td></tr> <tr><td>2</td><td>Rail</td></tr> <tr><td>3</td><td>Bus</td></tr> <tr><td>4</td><td>Ferry</td></tr> <tr><td>5</td><td>Cable car</td></tr> <tr><td>6</td><td>Gondola, Suspended cable car</td></tr> <tr><td>7</td><td>Funicular</td></tr> </tbody> </table>

## Setup

### Using uv

Installing uv (if necessary):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create a virtual environment and install dependencies:

```bash
uv venv
```

Activate the virtual environment:

On Linux and macOS:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
uv pip install -r requirements.txt
```

## Setup Environment variables

```bash
cp env.example .env
```

Edit ".env" file if needed

## Usage

To run the ETL, use the following command:

```bash
uv run python run_etl.py
```


## Testing

```bash
uv run pytest
```

Run pytest with coverage

```bash
uv run pytest --cov=src --cov-report=html tests/
```

## Pylint

```bash
uv run pylint src/
```

## Ruff
```bash
uv run ruff format src/
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Create a new Pull Request


## License

This project is licensed under the MIT License.
