# Navien NWP500

<!-- WIP: Documentation is still in progress -->

Home Assistant integration to monitor (read only, no control!) Navien NWP500 heat pump water heaters via your NaviLink account. Provides real-time temperature, energy usage, and operational status.


## Installation  

### 1. Install HACS (if not already installed)  
Follow the [HACS installation guide](https://hacs.xyz/).  

### 2. Add MBTALive to HACS  
1. Open **Home Assistant → HACS**.  
2. Click the three dots (top-right) → **Custom repositories**.  
3. Add `https://github.com/chiabre/navien_nwp500` under **Repository** as an **Integration**.  
4. Click **Add**.  

### 3. Install Navien NWP500  
1. Find **Navien NWP500** in HACS.  
2. Click **Install** and choose a version

### 4. Configure the Integration  
1. Restart Home Assistant.  
2. Go to **Settings → Devices & Services → + Add Integration**.  
3. Search for **Navien NWP500** and enter **Navien Link Username & Password:**
4. Select the Navien NWP500 water heater(s) linked to your account that you want to monitor
5. Selcect the update frequency 

## Updating  

HACS will notify you when an update is available. To update:  
1. Go to **HACS → Navien NWP50**.  
2. Click **Update**.  
3. Restart Home Assistant.  

## Contributing  

Contributions are welcome! Feel free to open an issue or submit a pull request.  

## Support  

For help, open an issue in this GitHub repository.  
