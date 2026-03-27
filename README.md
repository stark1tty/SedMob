<img src="media/banner/core.jpg" alt="SedMob Banner" width="500"/>

# SedMob

A free and open-source web application for field geological and sedimentological core logging.

SedMob lets geologists create sedimentary logs in the field using any device with a browser. Create unlimited logs, record detailed bed-by-bed data, and export to CSV compatible with [SedLog](https://sedlog.rhul.ac.uk/) for desktop visualization.

## Features

- Create and manage multiple sedimentary log profiles with GPS metadata
- Record detailed bed data: lithology (up to 3 components), grain size (clastic and carbonate), sedimentary structures, bioturbation, boundaries, paleocurrents, and facies
- Drag-and-drop bed reordering
- CSV export compatible with SedLog
- Customizable reference data (lithologies, structures, grain sizes, boundaries)
- Pre-seeded with standard sedimentological classification schemes
- SQLite database, no external services required

## Getting Started

### Requirements

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/stark1tty/SedMob.git
cd SedMob

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r sedmob/requirements.txt

# Run the application
python run.py
```

The app will be available at `http://localhost:5000`.

### Running Tests

```bash
pytest
```

## Screenshots

<table>
  <tr>
    <td><img src="media/screenshots/Screenshot_20230419-105712.png" alt="Main Menu" width="150" height="300"><br>Main Menu</td>
    <td><img src="media/screenshots/Screenshot_20230419-105720.png" alt="Core Details" width="150" height="300"><br>Core Details</td>
    <td><img src="media/screenshots/Screenshot_20230419-105729.png" alt="Core Log" width="150" height="300"><br>Core Log</td>
  </tr>
  <tr>
    <td><img src="media/screenshots/Screenshot_20230419-105737.png" alt="Core Log" width="150" height="300"><br>Core Log</td>
    <td><img src="media/screenshots/Screenshot_20230419-105741.png" alt="Core Log" width="150" height="300"><br>Core Log</td>
    <td><img src="media/screenshots/Screenshot_20230424-134429.png" alt="Settings Menu" width="150" height="300"><br>Settings Menu</td>
  </tr>
</table>

## Roadmap

- [ ] Dark mode / UI improvements
- [ ] Default menu options for standard sedimentological recording (including Tröels-Smith 1955)
- [ ] Colour recording menu
- [ ] Core metadata fields (client, project, etc.)
- [ ] Gallery / photo attachments
- [ ] Additional export options (Dropbox, email, RockWorks)
- [ ] Server synchronization
- [ ] SedLog-style graphical previews
- [ ] New sheet types: day sheets, trench pits, test pits, misc notes

## Background

SedMob was originally developed as a Cordova-based mobile app by [Pawel Wolniewicz](https://github.com/pwlw/SedMob). This version is a rewrite as a Python/Flask web application, designed to run on any device with a browser.

## References

Wolniewicz, P. (2014). SedMob: A mobile application for creating sedimentary logs in the field. *Computers & Geosciences*, 66, 10.1016/j.cageo.2014.02.004.

## License

Open source. See the repository for license details.
