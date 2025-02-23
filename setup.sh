#!/bin/bash

# Instalar Playwright y sus dependencias
python -m pip install --upgrade pip
python -m pip install playwright
playwright install chromium
python -m playwright install-deps chromium