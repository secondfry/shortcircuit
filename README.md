# Short Circuit

## Description
Short Circuit (previously known as Pathfinder) is a desktop application which is able to find the shortest path between solar systems (including wormholes) using data retrieved from Eve SDE and 3rd party wormhole mapping tools. The application is able to run on all systems where Python 3.10 and PySide2 are supported.

**Features:**

1. Ability to add wormhole connections from [Tripwire](https://tripwire.eve-apps.com/).
2. ESI authentication for reading the player location and setting the destination in-game.
3. Avoidance list.
4. Wormhole restrictions for: size, life, mass, last updated.
5. Instructions specify the signature and type of the wormhole (makes navigation easier).
6. One-line output which can be copy-pasted for those lazy fleet members.

## Usage
```bash
$ pip install pipenv
$ mkdir .venv
$ pipenv install
$ pipenv shell
$ cd src
$ python main.py
```

Some users reported having troubles when installing PySide on Linux/Mac. Try using your built-in package manager. Example for *debian-based* systems:
```bash
$ sudo apt-get install python-pyside
```

For *Arch Linux* users: Short Circuit is available on [AUR](https://aur.archlinux.org/packages/shortcircuit/) (Credits to [Sanxion](https://gate.eveonline.com/Profile/Sanxion)):
```bash
yaourt -S shortcircuit
```

## Releases
Binaries (executables) can be downloaded from [here](https://github.com/secondfry/shortcircuit/releases).

## SDE update
In case of SDE update, get new `mapLocationWormholeClasses.csv`,
`mapSolarSystemJumps.csv`, `mapSolarSystems.csv` from
https://www.fuzzwork.co.uk/dump/latest/ and overwrite ones in `src/database`.  
Thank you, @fuzzysteve (Steve Ronuken).

## About ESI
Using ESI is optional, but it provides features like getting current player location or setting in-game destination automatically.

Short Circuit uses implicit mode which only allows for a 20 minutes session, after that you have to relog. If you don't want to use the "implicit" mode, you will have to port back using your own keys feature.

## Eve-Scout
![TripwireConfig](http://i.imgur.com/GiJ2zc3.png)

If you enable Eve-Scout option then wormhole connections to/from Thera updated by [Eve-Scout](https://www.eve-scout.com/) will be retrieved, also. However, if you use the public Tripwire server, which is `https://tripwire.eve-apps.com/`, then there's no need to enable this option because Eve-Scout is updating Thera connections on the public Tripwire server automatically.

This is only useful if you or your corp/alliance have their own Tripwire server.

## Security prioritization
Security prioritization mechanism is defined by four values which represent a weight, or an effort:

* HS - the amount of effort it takes to jump a gate to high-sec.
* LS - the amount of effort it takes to jump a gate to low-sec.
* NS - the amount of effort it takes to jump a gate to null-sec.
* WH - the amount of effort it takes to jump a wormhole to any system.

Values may range from 1 to 100 and if all values are equal (ex. all equal to 1), then this function is practically disabled.

![SecPrio](https://i.imgur.com/wUaSe3e.png)

In the above scenario the user specified that the effort is the same for taking gates to high-sec or low-sec and there's no need to prioritize one above the other. Compared to this, it's ten times more difficult to take gates to null-sec and three times more difficult to take any wormholes compared to high-sec/low-sec gates.

For example, this may be useful when trying to avoid null-sec systems if possible, unless it shortens the path considerably, and when wormholes aren't bookmarked.

## Screenshot
![Screenshot](https://i.imgur.com/1NjxSP9.png)

## Video
<a href="http://www.youtube.com/watch?feature=player_embedded&v=oM3mSKzZM0w" target="_blank"><img src="http://img.youtube.com/vi/oM3mSKzZM0w/0.jpg" alt="Short Circuit video" width="480" height="360" border="10" /></a>

## How it works
Short Circuit reconstructs its own version of the Eve solar map from the 'mapSolarSystemJumps' table of the Static Data Export database. After that, the solar map can be extended by retrieving connections from popular 3rd party wormhole mapping tools. The JSON response from [Tripwire](https://tripwire.eve-apps.com/) is processed and the connections are added to the existing solar map. Graph algorithms will compute the shortest path taking certain things into account like avoidance list and wormhole size restrictions.

Sample JSON response from Tripwire (converted to YAML for easy reading). This type of response is processed and added to the application's own solar system representation:
```yaml
esi:
  "91435934":
    characterID: "91435934"
    characterName: "Lenai Chelien"
    accessToken: "eyJhbGci..."
    refreshToken: "OWqksY8..."
    tokenExpire: "2026-02-13 18:29:03"
sync: "Feb 13, 2026 18:21:12 +0000"
signatures:
  "2175524":
    id: "2175524"
    signatureID: "???"
    systemID: "30002659"
    type: "wormhole"
    name: ""
    bookmark: null
    lifeTime: "2026-02-13 18:16:10"
    lifeLeft: "2026-02-16 18:16:10"
    lifeLength: "259200"
    createdByID: "91435934"
    createdByName: "Lenai Chelien"
    modifiedByID: "91435934"
    modifiedByName: "Lenai Chelien"
    modifiedTime: "2026-02-13 18:16:15"
    maskID: "98524402.2"
  "2175525":
    id: "2175525"
    signatureID: "???"
    systemID: "30000144"
    type: "wormhole"
    name: ""
    bookmark: null
    lifeTime: "2026-02-13 18:16:10"
    lifeLeft: "2026-02-16 18:16:10"
    lifeLength: "259200"
    createdByID: "91435934"
    createdByName: "Lenai Chelien"
    modifiedByID: "91435934"
    modifiedByName: "Lenai Chelien"
    modifiedTime: "2026-02-13 18:16:15"
    maskID: "98524402.2"
wormholes:
  "629720":
    id: "629720"
    initialID: "2175524"
    secondaryID: "2175525"
    type: ""
    parent: ""
    life: "stable"
    mass: "stable"
    maskID: "98524402.2"
flares:
  flares: []
  last_modified: "02/13/2026 18:21:11 UTC"
proccessTime: "0.0148"
discord_integration: false
```

## EvE Online CREST API Challenge
*Pathfinder* (now renamed to *Short Circuit*) won the EvE Online CREST API Challenge 2016!

<https://community.eveonline.com/news/dev-blogs/winners-of-the-eve-online-api-challenge/>

<a href="https://www.youtube.com/watch?v=qw0OhRGeDgA&t=7m0s" target="_blank"><img src="http://img.youtube.com/vi/qw0OhRGeDgA/1.jpg" alt="Pathfinder on the o7 Show" width="480" height="360" border="10" /></a>

## Future development
1. Add support for more 3rd party wormhole mapping tools.
2. Combine data from multiple sources (multiple Tripwire accounts, etc.).
3. Suggestions?

## Contacts
For any questions please contact Lenai Chelien. I accept PLEX, ISK, Exotic Dancers and ~~drugs~~ boosters.
