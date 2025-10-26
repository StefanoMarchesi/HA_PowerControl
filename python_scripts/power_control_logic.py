from homeassistant.core import Context

CONTEXT_ID = "HA_POWER_CONTROL_CONTEXT"
logger = hass.get_logger(__name__)

# Create a static context for all service calls
my_context = Context(id=CONTEXT_ID)

def get_entity_state(entity_id):
    """Safely get the state of an entity from Home Assistant."""
    state = hass.states.get(entity_id)
    if state is None:
        logger.debug(f"PowerControl: Entity '{entity_id}' not found.")
        return None
    if state.state in ["unknown", "unavailable"]:
        logger.debug(f"PowerControl: Entity '{entity_id}' is {state.state}.")
        return None
    return state

# The 'action' parameter determines whether to reduce or restore power.
action = data.get("action")

if action == "reduce":
    logger.info("PowerControl: Starting load reduction logic.")

    # Scan loads in reverse priority order (20 down to 1)
    for i in range(20, 0, -1):
        switch_entity_id_helper = f"input_text.carico_{i}_switch"
        azione_entity_id_helper = f"input_select.azione_carico_{i}"
        temp_entity_id_helper = f"input_number.temp_pre_gestione_{i}"
        sospesa_entity_id_helper = f"input_number.potenza_{i}_sospesa"

        switch_entity_id_state = get_entity_state(switch_entity_id_helper)
        if not switch_entity_id_state or switch_entity_id_state.state == "Seleziona":
            continue

        switch_entity_id = switch_entity_id_state.state
        entity_domain = switch_entity_id.split('.')[0]

        entity_state = get_entity_state(switch_entity_id)
        if not entity_state or entity_state.state == 'off':
            continue

        azione_state = get_entity_state(azione_entity_id_helper)
        if not azione_state: continue
        azione = azione_state.state

        action_performed = False

        # --- Priority 1: Adjust Climate Temperature if set to "Auto" ---
        if entity_domain == 'climate' and azione == 'Auto':
            temp_saved_state = get_entity_state(temp_entity_id_helper)

            # A saved temp > 0 means we've already managed this entity.
            if temp_saved_state and float(temp_saved_state.state) > 0:
                continue

            attributes = entity_state.attributes
            original_temp = attributes.get('temperature')
            min_temp = attributes.get('min_temp', 16.0) # Default fallback
            max_temp = attributes.get('max_temp', 30.0) # Default fallback

            if original_temp is not None:
                new_temp = None
                if entity_state.state == 'cool':
                    new_temp = original_temp + 2.0
                    # Clamp the new temperature to the maximum allowed
                    new_temp = min(new_temp, max_temp)
                elif entity_state.state == 'heat':
                    new_temp = original_temp - 2.0
                    # Clamp the new temperature to the minimum allowed
                    new_temp = max(new_temp, min_temp)

                if new_temp is not None:
                    logger.info(f"PowerControl: Reducing load for {switch_entity_id}. Adjusting temp from {original_temp} to {new_temp} (Limits: {min_temp}-{max_temp}).")

                    # Save the original temperature to mark it as "managed"
                    hass.services.call('input_number', 'set_value', {'entity_id': temp_entity_id_helper, 'value': original_temp}, context=my_context)

                    # Set the new, clamped temperature
                    hass.services.call('climate', 'set_temperature', {'entity_id': switch_entity_id, 'temperature': new_temp}, context=my_context)
                    action_performed = True

        # --- Priority 2: Turn off devices ---
        elif azione == 'Spegni' or (entity_domain in ['switch', 'light'] and azione == 'Auto'):
            power_sensor_id_helper = f"input_text.carico_{i}_potenza"
            power_sensor_id_state = get_entity_state(power_sensor_id_helper)
            if power_sensor_id_state:
                power_state = get_entity_state(power_sensor_id_state.state)
                if power_state and float(power_state.state) > 10:
                    logger.info(f"PowerControl: Reducing load for {switch_entity_id} by turning it off.")
                    hass.services.call('input_number', 'set_value', {'entity_id': sospesa_entity_id_helper, 'value': power_state.state}, context=my_context)
                    hass.services.call(entity_domain, "turn_off", {'entity_id': switch_entity_id}, context=my_context)
                    action_performed = True

        if action_performed:
            logger.info("PowerControl: Action performed, ending current reduction cycle.")
            break

elif action == "restore":
    logger.info("PowerControl: Starting single-pass load restore logic.")

    action_performed = False

    # Scan in priority order (1 to 20)
    for i in range(1, 21):
        mantieni_spento_helper = f"input_boolean.mantini_spento_{i}"
        mantieni_spento_state = get_entity_state(mantieni_spento_helper)

        # --- PRE-CHECK: Skip if "Mantieni Spento" is enabled for this load ---
        if mantieni_spento_state and mantieni_spento_state.state == 'on':
            logger.debug(f"PowerControl: Skipping restore for carico_{i} because 'Mantieni Spento' is on.")
            continue

        switch_entity_id_helper = f"input_text.carico_{i}_switch"
        azione_entity_id_helper = f"input_select.azione_carico_{i}"
        temp_entity_id_helper = f"input_number.temp_pre_gestione_{i}"
        sospesa_entity_id_helper = f"input_number.potenza_{i}_sospesa"

        switch_entity_id_state = get_entity_state(switch_entity_id_helper)
        if not switch_entity_id_state or switch_entity_id_state.state == "Seleziona":
            continue

        switch_entity_id = switch_entity_id_state.state
        entity_domain = switch_entity_id.split('.')[0]

        azione_state = get_entity_state(azione_entity_id_helper)
        if not azione_state: continue
        azione = azione_state.state

        # --- Check 1: Restore Climate Temperature ---
        if entity_domain == 'climate' and azione == 'Auto':
            temp_saved_state = get_entity_state(temp_entity_id_helper)
            if temp_saved_state and float(temp_saved_state.state) > 0:
                original_temp = float(temp_saved_state.state)
                logger.info(f"PowerControl: Restoring climate {switch_entity_id} temperature to {original_temp}.")

                hass.services.call('climate', 'set_temperature', {'entity_id': switch_entity_id, 'temperature': original_temp}, context=my_context)
                hass.services.call('input_number', 'set_value', {'entity_id': temp_entity_id_helper, 'value': 0}, context=my_context)

                action_performed = True

        # --- Check 2: Turn On Device ---
        if not action_performed:
            sospesa_state = get_entity_state(sospesa_entity_id_helper)
            if sospesa_state and float(sospesa_state.state) > 0:
                if azione == 'Spegni' or (azione == 'Auto' and entity_domain in ['switch', 'light']):
                    logger.info(f"PowerControl: Restoring device {switch_entity_id} by turning it on.")

                    hass.services.call(entity_domain, "turn_on", {'entity_id': switch_entity_id}, context=my_context)
                    hass.services.call('input_number', 'set_value', {'entity_id': sospesa_entity_id_helper, 'value': 0}, context=my_context)

                    action_performed = True

        if action_performed:
            logger.info("PowerControl: Restore action performed, ending current cycle.")
            break

    if not action_performed:
        logger.info("PowerControl: No loads to restore in this cycle.")

else:
    logger.warning(f"PowerControl: Invalid action '{action}' received.")
