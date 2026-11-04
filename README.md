<!-- ha-marketplace:exclude-start -->
# Absolute Humidity helpers for Home Assistant

⚠️ Early development, use at your own risk.

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]]()
[![License][license-shield]](LICENSE)

<!-- ha-marketplace:exclude-end -->
Creates helpers that watch a temperature and relative humidity sensor and calculates absolute humidity in g/m³ with attributes for comfort and condensation risk.

_Please ⭐ this repo on [GitHub][repository] if you find it useful._

_If you want to show your support please_

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/codechimp)

### Attributes

**Comfort**

| Value | Absolute humidity |
| --- | --- |
| very_dry | Below 5 g/m³ |
| dry | 5 to below 7 g/m³ |
| comfortable | 7 to below 10 g/m³ |
| humid | 10 through 12 g/m³ |
| very_humid | Above 12 g/m³ |

**Condensation risk**

| Value | Absolute humidity |
| --- | --- |
| low | Below 10.4 g/m³ |
| moderate | 10.4 to below 12.1 g/m³ |
| high | 12.1 g/m³ and above |

Condensation risk is an estimate from air humidity. Actual condensation depends on surface temperature, which these two sources do not measure. The thresholds are simple indicators, rather than a calculation of surface condensation.

Why absolute humidity? Most humidity sensors report relative humidity, which is useful for assessing comfort alongside temperature. However, relative humidity alone can be misleading when comparing areas at different temperatures. Absolute humidity measures the amount of water vapour per cubic metre of air, making it more useful for comparing moisture levels indoors and outdoors, or between rooms. This can help you decide when ventilation is likely to reduce indoor moisture and, alongside temperature readings, when it may help cool your home.

![Helper Creation](https://raw.githubusercontent.com/andrew-codechimp/HA-Absolute_Humidity/main/images/helper-create.png "Helper Creation")

<!-- ha-marketplace:exclude-start -->
### Installation

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=andrew-codechimp&repository=ha-absolute-humidity&category=integration)

Or search for Absolute Humidity within Marketplace.

A new Absolute Humidity helper will be available within Settings/Helpers or click the My link to jump straight there

[![Open your Home Assistant instance and start setting up a new helper.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=absolute_humidity)
<!-- ha-marketplace:exclude-end -->

---

[repository]: https://github.com/andrew-codechimp/HA-Absolute-Humidity
[commits-shield]: https://img.shields.io/github/commit-activity/y/andrew-codechimp/HA-Absolute-Humidity.svg?style=for-the-badge
[commits]: https://github.com/andrew-codechimp/HA-Absolute-Humidity/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/andrew-codechimp/HA-Absolute-Humidity.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/andrew-codechimp/HA-Absolute-Humidity.svg?style=for-the-badge
[releases]: https://github.com/andrew-codechimp/HA-Absolute-Humidity/releases
[download-latest-shield]: https://img.shields.io/github/downloads/andrew-codechimp/HA-Absolute-Humidity/latest/total?style=for-the-badge
[hacs-installs-shield]: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fabsolute_humidity&style=for-the-badge
