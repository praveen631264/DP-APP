
import time
import json
import os
import logging
import logging_config
import document_store
import notification_service
from collections import deque

# --- Logging Setup ---
logging_config.setup_logging()
logger = logging.getLogger(__name__)

# --- Agent Configuration ---
LOG_FILE_PATH = 'logs/app.log'
HEARTBEAT_INTERVAL = 10 # Seconds
SELF_HEAL_COOLDOWN = 60 # Seconds to wait after a self-heal action
MAX_RECENT_LINES = 1000 # Max lines to keep in memory to avoid duplicates

# --- Self-Healing Ruleset ---
# This can be expanded with more sophisticated rules.
SELF_HEAL_RULES = {
    "api_request_failed": {
        "keywords": ["API request failed"],
        "action": "acknowledge_and_cooldown",
        "cooldown_until": 0 # Timestamp until which this rule is on cooldown
    }
}

# --- Core Agent Logic ---

def follow(file):
    """Generator function that yields new lines from a file."""
    file.seek(0, os.SEEK_END) # Go to the end of the file
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.1) # Sleep briefly
            continue
        yield line

def process_log_line(line: str, recent_lines: deque):
    """Parses a single log line and takes action if it's a new error."""
    try:
        log_entry = json.loads(line)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse log line: {line}")
        return

    # Check for errors and avoid processing duplicates
    if log_entry.get('level') == 'ERROR' and line not in recent_lines:
        recent_lines.append(line)
        logger.info(f"New ERROR detected: {log_entry.get('message')}")
        handle_error(log_entry)

def handle_error(log_entry: dict):
    """Decides whether to self-heal or escalate an error."""
    message = log_entry.get('message', '').lower()
    
    # 1. Check for Self-Healing Opportunities
    for rule_name, rule in SELF_HEAL_RULES.items():
        if any(keyword in message for keyword in rule['keywords"]):
            if time.time() > rule['cooldown_until']:
                logger.info(f"Matched self-heal rule: '{rule_name}'. Taking action.")
                rule['cooldown_until'] = time.time() + SELF_HEAL_COOLDOWN
                # For now, the only action is to log it. This could be a script call.
                document_store.create_incident_record(
                    log_line=json.dumps(log_entry),
                    error_type=rule_name,
                    status="self_healed_acknowledged"
                )
                logger.info(f"Self-heal action complete. Rule '{rule_name}' is on cooldown for {SELF_HEAL_COOLDOWN} seconds.")
                return # Stop further processing
            else:
                logger.info(f"Matched self-heal rule '{rule_name}' but it is on cooldown. Ignoring.")
                return

    # 2. If no self-heal rule matched, Escalate
    logger.info("No self-heal rule matched. Escalating to create a new incident.")
    escalate_and_notify(log_entry)

def escalate_and_notify(log_entry: dict):
    """Creates an incident record and sends notifications."""
    log_line_str = json.dumps(log_entry)
    error_type = log_entry.get('message', 'Unknown Error')[:50] # Truncate for summary

    # Create the persistent incident record
    incident = document_store.create_incident_record(
        log_line=log_line_str,
        error_type=error_type,
        status="new_incident"
    )
    incident_id = incident['incident_id']
    logger.info(f"New incident record created: {incident_id}")

    # Trigger notifications (simulated)
    subject = f"New Incident Detected: {incident_id}"
    body = f"A new incident has been recorded.\nID: {incident_id}\nError Type: {error_type}\nLog Line: {log_line_str}"
    
    notification_service.send_email("oncall-engineer@example.com", subject, body)
    notification_service.send_sms("+15551234567", f"New Incident: {incident_id} - {error_type}")
    notification_service.send_whatsapp("user_oncall_whatsapp_id", f"New Incident: {incident_id}")

    logger.info(f"All notifications sent for incident {incident_id}.")

# --- Main Agent Loop ---

def main():
    logger.info("--- Bugger Monitoring Agent Started ---")
    logger.info(f"Watching log file: {LOG_FILE_PATH}")
    
    # Use a deque for efficient fixed-size storage
    recent_lines = deque(maxlen=MAX_RECENT_LINES)

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as logfile:
            # Read existing lines into the recent_lines buffer to avoid refiring alerts on startup
            for line in logfile:
                recent_lines.append(line)
            logger.info(f"Seeded agent with {len(recent_lines)} existing log lines.")

            log_lines = follow(logfile)
            for line in log_lines:
                process_log_line(line, recent_lines)

    except FileNotFoundError:
        logger.error(f"Log file not found at {LOG_FILE_PATH}. Agent will exit.")
        # In a real system, you might want to wait for the file to be created.
    except Exception as e:
        logger.critical(f"An unhandled exception occurred in the agent: {e}", exc_info=True)
        time.sleep(10) # Wait before restarting to avoid rapid-fire crashes

if __name__ == "__main__":
    main()
