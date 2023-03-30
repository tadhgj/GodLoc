# GodLoc
Records TransLoc bus locations and stores them in a json file.

# fourth.py
## Usage 

```python3 fourth.py```

### What does it do?

From 4AM to 2AM, this records Rutgers bus locations every 5 seconds and stores them in a json file.

In more technical terms:
Sends a request to the TransLoc API every 5 seconds, stores the data in a json file with the date formatted. Leaves two log files:
* `test.log` - so you can run tail -f test.log and see the output
* `EST_%Y-%m-%d_%H:%M:%S_busThird.log` - so you can view previous logs

The bus data file is formatted as `busData-YYYY-MM-DD.json`

(you can customize the locations of these files with outputDir)

### Why?

Transloc has a great website, it's actually very usable, robust, and fast. It's only limitation is that it only displays realtime data.

Because re-inventing the wheel is fun, I decided to make a historical API.

With this data, I hope that I can answer some questions like:
* How long do Rutgers bus drivers actually spend on their breaks?
* When can I realistically expect the first and last bus of the day for any given route?



### Notable libraries used

* ujson (optional, faster than regular python json library) - I needed this to run it at a 5 second interval on a particularly low end VPS
* pytz (timezone support) - I run my script on a server outside my timezone, so I needed this

# fetchRoutes.py
## Usage

```python3 fetchRoutes.py```

### What does it do?

Fetches routes, stops, and segments from the TransLoc API and stores them in 3 json files.

### Why?

Some data does not change, like route names and segments. Also, I just wanted to never have to deal with Google's polyline encoding again. 


### Notable libraires used

* polyline (for decoding polyline segments - hint, they're encoded with Google's polyline algorithm. That's what that gibberish is.)

---

# Footnotes

## Requirements

* Your own API key from TransLoc (free)
* Python 3.something I believe

## License

It's my code. Have fun & make something cool. Credit me.

(legally)
GNU General Public License v3.0
See LICENSE for more information.

## Author

Tadhg Jarzebowski

## Acknowledgements

* TransLoc for providing a free API with (basically) no rate limits
* ChatGPT actually told me it was Google's polyline decoding
