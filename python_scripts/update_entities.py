# Determine if filtering is enabled
filtering_enabled_state = hass.states.get('input_boolean.selezione_script_python')
filtering_enabled = filtering_enabled_state.state == 'on' if filtering_enabled_state else False

# --- Get Filter Values from Helpers ---
switch_filter = hass.states.get('input_text.pc_switch_filter').state or 'switch.'
light_filter = switch_filter.replace('switch.', 'light.') # Also apply switch filter to lights
climate_filter = hass.states.get('input_text.pc_climate_filter').state or 'climate.'
sensor_filter = hass.states.get('input_text.pc_sensor_filter').state or 'sensor.'

# --- Populate Switch/Light/Climate Entities ---
all_switches = ["Seleziona"]
switch_domains = ['switch', 'light', 'climate']

for domain in switch_domains:
    entities = hass.states.entity_ids(domain)
    if filtering_enabled:
        if domain == 'switch':
            all_switches.extend([e for e in entities if e.startswith(switch_filter)])
        elif domain == 'light':
            all_switches.extend([e for e in entities if e.startswith(light_filter)])
        elif domain == 'climate':
            all_switches.extend([e for e in entities if e.startswith(climate_filter)])
    else:
        all_switches.extend(entities)

# Update all 20 load switch input_selects
for i in range(1, 21):
    entity_id = f"input_select.carico_{i}_switch"
    service_data = {'entity_id': entity_id, 'options': sorted(all_switches)}
    hass.services.call('input_select', 'set_options', service_data)

# --- Populate Sensor Entities ---
all_sensors = ["Seleziona"]
sensor_entities = hass.states.entity_ids('sensor')

if filtering_enabled:
    all_sensors.extend([e for e in sensor_entities if e.startswith(sensor_filter)])
else:
    all_sensors.extend(sensor_entities)

# Update all 20 load power sensor input_selects
for i in range(1, 21):
    entity_id = f"input_select.carico_{i}_potenza"
    service_data = {'entity_id': entity_id, 'options': sorted(all_sensors)}
    hass.services.call('input_select', 'set_options', service_data)

# Update the main power sensor input_select
service_data = {'entity_id': 'input_select.potenza_carichi', 'options': sorted(all_sensors)}
hass.services.call('input_select', 'set_options', service_data)
