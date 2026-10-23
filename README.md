# Absolute Humidity

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]]()
[![HACS Installs][hacs-installs-shield]]()
[![License][license-shield]](LICENSE)

Absolute Humidity Helpers for Home Assistant **2026.11.0.dev0**

## Overview

Creates a helper that watches a temperature and relative humidity sensor and calculates absolute humidity in **g/m³**.


### Attributes

Comfort is assessed from the calculated absolute humidity:

| Attribute | Value | Absolute humidity |
| --- | --- | --- |
| `comfort` | `very_dry` | Below 5 g/m³ |
| `comfort` | `dry` | 5 to below 7 g/m³ |
| `comfort` | `comfortable` | 7 to below 10 g/m³ |
| `comfort` | `humid` | 10 through 12 g/m³ |
| `comfort` | `very_humid` | Above 12 g/m³ |

Condensation risk is also assessed from the calculated absolute humidity:

| Attribute | Value | Absolute humidity |
| --- | --- | --- |
| `condensation_risk` | `low` | Below 10.4 g/m³ |
| `condensation_risk` | `moderate` | 10.4 to below 12.1 g/m³ |
| `condensation_risk` | `high` | 12.1 g/m³ and above |

Condensation risk is an estimate from air humidity. Actual condensation depends on surface temperature, which these two sources do not measure. The thresholds are simple indicators, rather than a calculation of surface condensation.

_Please :star: this repo if you find it useful_

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/codechimp)

![Helper Creation](https://raw.githubusercontent.com/andrew-codechimp/ha-absolute_humidity/main/images/helper-create.png "Helper Creation")

## Installation

### Marketplace

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=andrew-codechimp&repository=HA-Absolute-Humidity&category=Integration)

Or search for it within Marketplace if My Home Assistant does not work for you

Restart Home Assistant

In the HA UI go to "Configuration" -> "Devices & services" -> "Helpers" click "+" and select "Absolute Humidity"

### Manual Installation

<details>
<summary>Show detailed instructions</summary>

Installation via Marketplace is recommended, but a manual setup is supported.

1. Manually copy custom_components/absolute_humidity folder from latest release to custom_components folder in your config folder.
1. Restart Home Assistant.
1. In the HA UI go to "Configuration" -> "Devices & services" -> "Helpers" click "+" and select "Absolute Humidity"

</details>

A new Absolute Humidity helper will be available within Settings/Helpers or click the My link to jump straight there

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=absolute_humidity)

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/andrew-codechimp/HA-Absolute-Humidity.svg?style=for-the-badge
[commits]: https://github.com/andrew-codechimp/HA-Absolute-Humidity/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/andrew-codechimp/HA-Absolute-Humidity.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/andrew-codechimp/HA-Absolute-Humidity.svg?style=for-the-badge
[releases]: https://github.com/andrew-codechimp/HA-Absolute-Humidity/releases
[download-latest-shield]: https://img.shields.io/github/downloads/andrew-codechimp/HA-Absolute-Humidity/latest/total?style=for-the-badge
[hacs-installs-shield]: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fabsolute_humidity&style=for-the-badge
