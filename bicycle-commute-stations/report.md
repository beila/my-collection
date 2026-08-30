# Bicycle Commute Station Ranking

Research date: 2026-08-30

## Result

- Two workplace stations are within a routed 10-minute walk: Shoreditch High Street and Liverpool Street.
- The original 33 direct, circle-qualified stations remain unchanged.
- The expanded TfL route graph contains 657 physical stations that can reach a workplace station directly or with one same-group interchange.
- 109 non-original stations could theoretically beat Brockley under the pure-cycling speed bound; every one was independently routed.
- 19 additions are strictly faster than Brockley's retained 48.69-minute benchmark, producing 52 ranked map stations.
- Woolwich Arsenal is now #1 at 18.2 minutes, Woolwich is #2 at 19.7 minutes, and Abbey Wood is #3 at 20.8 minutes. Brockley is now #21.
- The full home-to-workplace route remains 83.2 minutes / 16.4 km with the independent router; TfL estimates 58 minutes / 17.22 km.
- [Open the interactive map](map.html).

## At-Most-One-Change Expansion

| Stage | Count |
|---|---:|
| TfL lines audited | 44 |
| Exact ordered route patterns | 1060 |
| Physical stations reachable with at most one change | 657 |
| Independently routed lower-bound candidates | 109 |
| Additions faster than Brockley | 19 |

The requested search groups are (1) Underground, Overground, Elizabeth line, and DLR together as **TfL PAYG rail**, and (2) **National Rail** alone. Every accepted one-change path keeps both legs inside one group and uses either the same NaPTAN station or a shared official TfL parent hub.

This grouping is not a fare guarantee. TfL's [Tube and rail fares](https://tfl.gov.uk/fares/find-fares/tube-and-rail-fares) page covers Tube, DLR, Overground, Elizabeth line, and National Rail together. Its [2026 adult fare table](https://tfl.gov.uk/cdn/static/cms/documents/adult-fares.pdf) says caps cover all four TfL modes and most National Rail services, with Southeastern high-speed and Heathrow Express excluded. Exact charging still depends on zones, route, operator, time, and recognized interchanges.

### Qualifying Additions

| New Rank | Station | Independent Cycle | Public Transport Path | Changes |
|---:|---|---:|---|---:|
| 1 | Woolwich Arsenal | 18.2 min / 4.25 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 |
| 3 | Abbey Wood | 20.8 min / 4.67 km | Elizabeth line direct to Liverpool Street | 0 |
| 4 | Lewisham | 37.1 min / 8.57 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |
| 5 | Elverson Road | 37.6 min / 8.81 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |
| 6 | King George V | 37.7 min / 6.27 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 |
| 7 | Cutty Sark (for Maritime Greenwich) | 39.5 min / 8.62 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |
| 8 | London City Airport | 39.8 min / 6.99 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 |
| 9 | Greenwich | 40 min / 8.71 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |
| 10 | Gallions Reach | 42.6 min / 7.42 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 |
| 11 | Pontoon Dock | 43.8 min / 7.98 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 |
| 12 | Cyprus | 43.9 min / 7.78 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 |
| 13 | North Greenwich | 43.9 min / 9.24 km | Jubilee to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |
| 14 | Deptford Bridge | 44 min / 9.69 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |
| 15 | Prince Regent | 46.2 min / 8.51 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 |
| 16 | Royal Albert | 46.8 min / 8.59 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 |
| 17 | Beckton Park | 47.4 min / 8.48 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 |
| 18 | Beckton | 47.6 min / 8.51 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 |
| 19 | West Silvertown | 47.8 min / 8.71 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 |
| 20 | Island Gardens | 48.1 min / 8.75 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 |

## Custom House Discrepancy

| Source | Duration | Distance | Route choice | Source route |
|---|---:|---:|---|---|
| TfL Journey Planner | 83 min | 23.97 km | Rides west to Tower Bridge, then back east | Not linked |
| OpenStreetMap.de bicycle router | 53.3 min | 9.31 km | Uses Woolwich Foot Tunnel | [Open route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.509769%2C0.02673) |
| Google Maps, user-observed | about 45 min | Not captured | Route geometry not captured; duration is consistent with a shorter strategy | Not captured |

TfL's 83-minute value is internally consistent with its 23.97 km route, but that route omits the direct Woolwich crossing and adds 14.66 km. The independent route resolves the detour and assigns 9.3 minutes to the 0.57 km Woolwich Foot Tunnel segment. The remaining difference from Google's approximate 45 minutes reflects speed, junction, and tunnel-access modelling. No Google Directions API response was available, so the observed value remains an approximate cross-check.

## Full Home-To-Workplace Ride

| Source | Duration | Distance | Route |
|---|---:|---:|---|
| OpenStreetMap.de bicycle router | 83.2 min | 16.4 km | [Open route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.52165%2C-0.077734375) |
| TfL Journey Planner | 58 min | 17.22 km | Not linked |

The independent route is the map's primary full-commute line and uses Greenwich Foot Tunnel. Similar distances but a 25.2-minute duration difference show materially different speed and access-penalty models; neither estimate is a guaranteed travel time.

## Workplace Stations

| Station | Walk | Distance | Within 10 Minutes |
|---|---:|---:|:---:|
| Shoreditch High Street Station | 2 min | 197 m | Yes |
| Liverpool Street Station | 5 min | 326 m | Yes |
| Aldgate East | 12 min | 849 m | No |
| Old Street Station | 13 min | 854 m | No |
| Hoxton Station | 16 min | 983 m | No |
| Moorgate Station | 16 min | 1059 m | No |
| Aldgate | 17 min | 1131 m | No |
| Fenchurch Street Station | 19 min | 1287 m | No |
| Bethnal Green Rail Station | 20 min | 1491 m | No |
| Bank | 21 min | 1334 m | No |
| Whitechapel Station | 21 min | 1502 m | No |
| Monument | 23 min | 1384 m | No |
| Tower Gateway Station DLR | 23 min | 1546 m | No |
| Tower Hill | 23 min | 1608 m | No |
| Barbican | 28 min | 1692 m | No |
| Cannon Street Station | 28 min | 1677 m | No |

## Circle Geometry

These circles apply only to the original 33 stations. Expansion additions are admitted solely by the one-change rule and the strict Brockley cycling threshold.

| Destination | Centre | Radius | Diameter |
|---|---|---:|---:|
| Liverpool Street | 51.492001, 0.003689 | 6.67 km | 13.33 km |
| Shoreditch High Street | 51.494715, 0.00765 | 6.56 km | 13.13 km |

## Ranked Stations

| Rank | Station | Scope | Independent Cycle | Public Transport Path | Changes | TfL Cycle Comparison | Route Links |
|---:|---|---|---:|---|---:|---:|---|
| 1 | Woolwich Arsenal | One-change expansion | 18.2 min / 4.25 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.490009%2C0.069127) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.490009%2C0.069127&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.490009%2C0.069127) |
| 2 | Woolwich | Original circle | 19.7 min / 4.4 km | Elizabeth line direct to Liverpool Street | 0 | 14 min / 4.4 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.492168%2C0.070593) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.492168%2C0.070593&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.492168%2C0.070593) |
| 3 | Abbey Wood | One-change expansion | 20.8 min / 4.67 km | Elizabeth line direct to Liverpool Street | 0 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.491284%2C0.121087) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.491284%2C0.121087&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.491284%2C0.121087) |
| 4 | Lewisham | One-change expansion | 37.1 min / 8.57 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.464665%2C-0.012874) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.464665%2C-0.012874&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.464665%2C-0.012874) |
| 5 | Elverson Road | One-change expansion | 37.6 min / 8.81 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.469074%2C-0.016728) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.469074%2C-0.016728&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.469074%2C-0.016728) |
| 6 | King George V | One-change expansion | 37.7 min / 6.27 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.502003%2C0.062624) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.502003%2C0.062624&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.502003%2C0.062624) |
| 7 | Cutty Sark (for Maritime Greenwich) | One-change expansion | 39.5 min / 8.62 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.481671%2C-0.01081) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.481671%2C-0.01081&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.481671%2C-0.01081) |
| 8 | London City Airport | One-change expansion | 39.8 min / 6.99 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.503416%2C0.048739) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.503416%2C0.048739&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.503416%2C0.048739) |
| 9 | Greenwich | One-change expansion | 40 min / 8.71 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.478087%2C-0.013673) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.478087%2C-0.013673&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.478087%2C-0.013673) |
| 10 | Gallions Reach | One-change expansion | 42.6 min / 7.42 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.508941%2C0.071555) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.508941%2C0.071555&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.508941%2C0.071555) |
| 11 | Pontoon Dock | One-change expansion | 43.8 min / 7.98 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.502212%2C0.032115) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.502212%2C0.032115&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.502212%2C0.032115) |
| 12 | Cyprus | One-change expansion | 43.9 min / 7.78 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.508473%2C0.063925) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.508473%2C0.063925&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.508473%2C0.063925) |
| 13 | North Greenwich | One-change expansion | 43.9 min / 9.24 km | Jubilee to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.50047%2C0.004287) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.50047%2C0.004287&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.50047%2C0.004287) |
| 14 | Deptford Bridge | One-change expansion | 44 min / 9.69 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.474215%2C-0.022438) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.474215%2C-0.022438&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.474215%2C-0.022438) |
| 15 | Prince Regent | One-change expansion | 46.2 min / 8.51 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.509263%2C0.034158) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.509263%2C0.034158&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.509263%2C0.034158) |
| 16 | Royal Albert | One-change expansion | 46.8 min / 8.59 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.508357%2C0.045935) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.508357%2C0.045935&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.508357%2C0.045935) |
| 17 | Beckton Park | One-change expansion | 47.4 min / 8.48 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.508793%2C0.054932) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.508793%2C0.054932&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.508793%2C0.054932) |
| 18 | Beckton | One-change expansion | 47.6 min / 8.51 km | DLR to Custom House (for ExCel), then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.514362%2C0.061453) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.514362%2C0.061453&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.514362%2C0.061453) |
| 19 | West Silvertown | One-change expansion | 47.8 min / 8.71 km | DLR to Stratford, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.502838%2C0.02246) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.502838%2C0.02246&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.502838%2C0.02246) |
| 20 | Island Gardens | One-change expansion | 48.1 min / 8.75 km | DLR to Canary Wharf, then Elizabeth line to Liverpool Street | 1 | Not fetched for expansion | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.487811%2C-0.010139) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.487811%2C-0.010139&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.487811%2C-0.010139) |
| 21 | Brockley | Original circle | 48.7 min / 11.06 km | Windrush direct to Shoreditch High Street | 0 | 41 min / 12.28 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.464649%2C-0.037537) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.464649%2C-0.037537&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.464649%2C-0.037537) |
| 22 | New Cross | Original circle | 49.5 min / 10.84 km | Windrush direct to Shoreditch High Street | 0 | 38 min / 11.12 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.476344%2C-0.032441) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.476344%2C-0.032441&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.476344%2C-0.032441) |
| 23 | New Cross Gate | Original circle | 51 min / 11.33 km | Windrush direct to Shoreditch High Street | 0 | 39 min / 11.73 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.475128%2C-0.040399) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.475128%2C-0.040399&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.475128%2C-0.040399) |
| 24 | Custom House | Original circle | 53.3 min / 9.31 km | Elizabeth line direct to Liverpool Street | 0 | 83 min / 23.97 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.509769%2C0.02673) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.509769%2C0.02673&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.509769%2C0.02673) |
| 25 | Honor Oak Park | Original circle | 54.2 min / 12.12 km | Windrush direct to Shoreditch High Street | 0 | 40 min / 11.97 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.449989%2C-0.045505) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.449989%2C-0.045505&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.449989%2C-0.045505) |
| 26 | Queens Road Peckham | Original circle | 55.9 min / 12.76 km | Windrush direct to Shoreditch High Street | 0 | 46 min / 13.65 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.473566%2C-0.057313) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.473566%2C-0.057313&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.473566%2C-0.057313) |
| 27 | Surrey Quays | Original circle | 59.3 min / 12.76 km | Windrush direct to Shoreditch High Street | 0 | 41 min / 12.16 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.493196%2C-0.047519) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.493196%2C-0.047519&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.493196%2C-0.047519) |
| 28 | Peckham Rye | Original circle | 60 min / 13.58 km | Windrush direct to Shoreditch High Street | 0 | 50 min / 14.65 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.470034%2C-0.069414) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.470034%2C-0.069414&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.470034%2C-0.069414) |
| 29 | Canada Water | Original circle | 61.3 min / 13.18 km | Windrush direct to Shoreditch High Street | 0 | 43 min / 12.89 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.49799%2C-0.04972) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.49799%2C-0.04972&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.49799%2C-0.04972) |
| 30 | East Ham | Original circle | 61.6 min / 11.62 km | Hammersmith & City direct to Liverpool Street | 0 | 95 min / 27.66 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.538948%2C0.051186) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.538948%2C0.051186&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.538948%2C0.051186) |
| 31 | West Ham | Original circle | 62.4 min / 12 km | Hammersmith & City direct to Liverpool Street | 0 | 81 min / 23.67 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.528136%2C0.005055) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.528136%2C0.005055&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.528136%2C0.005055) |
| 32 | Upton Park | Original circle | 62.5 min / 11.95 km | Hammersmith & City direct to Liverpool Street | 0 | 87 min / 25.44 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.53534%2C0.035263) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.53534%2C0.035263&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.53534%2C0.035263) |
| 33 | Rotherhithe | Original circle | 63.8 min / 13.74 km | Windrush direct to Shoreditch High Street | 0 | 44 min / 13.32 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.500817%2C-0.052048) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.500817%2C-0.052048&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.500817%2C-0.052048) |
| 34 | Canary Wharf | Original circle | 65.5 min / 11.97 km | Elizabeth line direct to Liverpool Street | 0 | 68 min / 20.05 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.506203%2C-0.018834) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.506203%2C-0.018834&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.506203%2C-0.018834) |
| 35 | Plaistow | Original circle | 66.6 min / 12.16 km | Hammersmith & City direct to Liverpool Street | 0 | 84 min / 24.31 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.531341%2C0.017451) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.531341%2C0.017451&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.531341%2C0.017451) |
| 36 | Bromley-by-Bow | Original circle | 68.7 min / 12.89 km | Hammersmith & City direct to Liverpool Street | 0 | 74 min / 21.7 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.524839%2C-0.011538) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.524839%2C-0.011538&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.524839%2C-0.011538) |
| 37 | Shadwell | Original circle | 72.7 min / 14.01 km | Windrush direct to Shoreditch High Street | 0 | 56 min / 16.77 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.511284%2C-0.056934) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.511284%2C-0.056934&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.511284%2C-0.056934) |
| 38 | Forest Gate | Original circle | 73.3 min / 14.25 km | Elizabeth line direct to Liverpool Street | 0 | 85 min / 24.91 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.549432%2C0.024353) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.549432%2C0.024353&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.549432%2C0.024353) |
| 39 | Stepney Green | Original circle | 73.6 min / 14.18 km | Hammersmith & City direct to Liverpool Street | 0 | 62 min / 18.36 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.521858%2C-0.046596) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.521858%2C-0.046596&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.521858%2C-0.046596) |
| 40 | Bow Road | Original circle | 73.7 min / 13.99 km | Hammersmith & City direct to Liverpool Street | 0 | 69 min / 20.18 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.52694%2C-0.025128) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.52694%2C-0.025128&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.52694%2C-0.025128) |
| 41 | Mile End | Original circle | 74.7 min / 14.26 km | Central direct to Liverpool Street | 0 | 68 min / 19.99 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.525122%2C-0.03364) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.525122%2C-0.03364&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.525122%2C-0.03364) |
| 42 | Stratford | Original circle | 75 min / 14.17 km | Elizabeth line direct to Liverpool Street | 0 | 78 min / 22.68 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.541508%2C-0.00241) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.541508%2C-0.00241&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.541508%2C-0.00241) |
| 43 | Wapping | Original circle | 75.2 min / 14.18 km | Windrush direct to Shoreditch High Street | 0 | 58 min / 17.37 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.504388%2C-0.055931) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.504388%2C-0.055931&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.504388%2C-0.055931) |
| 44 | Maryland | Original circle | 75.5 min / 14.54 km | Elizabeth line direct to Liverpool Street | 0 | 82 min / 23.64 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.546081%2C0.005815) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.546081%2C0.005815&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.546081%2C0.005815) |
| 45 | Whitechapel | Original circle | 75.7 min / 14.79 km | Elizabeth line direct to Liverpool Street | 0 | 59 min / 17.44 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.519498%2C-0.059858) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.519498%2C-0.059858&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.519498%2C-0.059858) |
| 46 | Tower Hill | Original circle | 77 min / 16.48 km | Circle direct to Liverpool Street | 0 | 54 min / 15.96 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.509971%2C-0.076546) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.509971%2C-0.076546&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.509971%2C-0.076546) |
| 47 | Bethnal Green (Underground) | Original circle | 78.2 min / 15.17 km | Central direct to Liverpool Street | 0 | 62 min / 18.46 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.527222%2C-0.055506) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.527222%2C-0.055506&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.527222%2C-0.055506) |
| 48 | Monument | Original circle | 79 min / 16.88 km | Circle direct to Liverpool Street | 0 | 55 min / 16.52 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.5107%2C-0.085969) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.5107%2C-0.085969&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.5107%2C-0.085969) |
| 49 | Bethnal Green (rail/Overground) | Original circle | 79.1 min / 15.26 km | Greater Anglia direct to Liverpool Street | 0 | 61 min / 18.06 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.523917%2C-0.059568) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.523917%2C-0.059568&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.523917%2C-0.059568) |
| 50 | Aldgate | Original circle | 79.4 min / 16.8 km | Circle direct to Liverpool Street | 0 | 55 min / 16.26 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.514246%2C-0.075689) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.514246%2C-0.075689&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.514246%2C-0.075689) |
| 51 | Aldgate East | Original circle | 80 min / 16.97 km | Hammersmith & City direct to Liverpool Street | 0 | 55 min / 16.35 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.515037%2C-0.072384) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.515037%2C-0.072384&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.515037%2C-0.072384) |
| 52 | Cambridge Heath | Original circle | 83.4 min / 15.91 km | Greater Anglia direct to Liverpool Street | 0 | 65 min / 19.13 km | [OpenStreetMap.de route](https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route=51.465997%2C0.090441%3B51.531973%2C-0.057279) / [Google route](https://www.google.com/maps/dir/?api=1&origin=51.465997%2C0.090441&destination=51.531973%2C-0.057279&travelmode=bicycling) / [Apple route](https://maps.apple.com/?saddr=51.465997%2C0.090441&daddr=51.531973%2C-0.057279) |

## Interpretation

- Home is the Postcodes.io centroid for `DA16 3QU`: `51.465997, 0.090441`.
- Workplace is the centre of recovered Plus Code `9C3XGWCC+Q8`: `51.521650, -0.077734`.
- OpenStreetMap.de's `routed-bike` profile supplies every selected duration. All mapped expansion routes contain only `cycling` and `pushing bike` steps.
- The selected durations are not elevation-adjusted. The published profile uses fixed route-tag speeds and penalties but does not read elevation, slope, or `incline`.
- TfL bicycle comparisons remain for the original 33 stations. No TfL bicycle value was fetched for the 19 expansion additions.
- Route-sequence reachability is not a live timetable guarantee. Check current service and the exact fare before travelling.

## Data Files

- [Ranked CSV](ranked-stations.csv)
- [Ranked JSON](ranked-stations.json)
- [One-change network](../intermediate/one-change-network.json)
- [One-change cycling audit](../intermediate/one-change-cycle-audit.json)
- [Fare-group audit](../intermediate/fare-group-audit.json)
- [Cycling source comparison CSV](../intermediate/cycle-route-comparison.csv)
- [Cycling source comparison JSON](../intermediate/cycle-route-comparison.json)
- [Map GeoJSON](map.geojson)
- [Interactive map](map.html)
- [Original request and operational interpretation](../input.md)
- [Methodology and source inventory](../methodology.md)
