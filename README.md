# Booking price monitor

This is a simple script that monitors the price for a list of Booking.com links every hour and:
- Store the price history in a CSV file
- Keeps screenshots of the pages
- Open an alert if the price drops

This is my first project done with Vibe Coding, ie do not write code, just ask Github Copilot to do it for me.

## Requirements

Only [uv](https://docs.astral.sh/uv/getting-started/installation/) as it will install all the dependencies for you.

It use QT so it is supposed to be working on Linux, OSX and Windows.

## Installation

```bash
uv run main.py
```
