# Get all switch, light, and climate entities
all_switches = ["Seleziona"]
all_switches.extend(hass.states.entity_ids('switch'))
all_switches.extend(hass.states.entity_ids('light'))
all_switches.extend(hass.states.entity_ids('climate'))

# Update all 20 load switch input_selects
for i in range(1, 21):
    entity_id = f"input_select.carico_{i}_switch"
    service_data = {'entity_id': entity_id, 'options': sorted(all_switches)}
    hass.services.call('input_select', 'set_options', service_data)

# Get all sensor entities
all_sensors = ["Seleziona"]
all_sensors.extend(hass.states.entity_ids('sensor'))

# Update all 20 load power sensor input_selects
for i in range(1, 21):
    entity_id = f"input_select.carico_{i}_potenza"
    service_data = {'entity_id': entity_id, 'options': sorted(all_sensors)}
    hass.services.call('input_select', 'set_options', service_data)

# Update the main power sensor input_select
service_data = {'entity_id': 'input_select.potenza_carichi', 'options': sorted(all_sensors)}
hass.services.call('input_select', 'set_options', service_data)
